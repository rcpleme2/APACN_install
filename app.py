"""
app.py
------
Servidor web Flask + Socket.IO para a automação de doação Nota Paraná.

Suporta até 5 sessões simultâneas. Cada sessão mantém um navegador Playwright
isolado enquanto o usuário estiver conectado.

Variáveis de ambiente:
  SECRET_KEY  – chave para assinar sessões Flask (obrigatória em produção)
  PORT        – porta a escutar (padrão: 5000)
"""

import os
import threading
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

from session_manager import SessionManager
from notaparana_bot import (
    abrir_navegador,
    fazer_login_portal,
    doar_lote,
    encerrar_sessao,
    CredenciaisInvalidasError,
)
from qr_collector import validar_chave, _extrair_chave

# ---------------------------------------------------------------------------
# Configuração do app
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-em-producao")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

session_manager = SessionManager(max_sessions=5)

# sid → {"pw", "browser", "page", "cnpj_verificado"}
_sessoes_browser: dict[str, dict] = {}
_sessoes_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Rotas HTTP
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Eventos Socket.IO
# ---------------------------------------------------------------------------

@socketio.on("validar_chave_web")
def handle_validar(data):
    entrada = data.get("entrada", "")
    chave = _extrair_chave(entrada)
    if not chave:
        emit("resultado_validacao", {"valida": False, "chave": None,
                                     "motivo": "Código não reconhecido"})
        return
    valida, motivo = validar_chave(chave)
    emit("resultado_validacao", {"valida": valida, "chave": chave, "motivo": motivo})


@socketio.on("fazer_login")
def handle_fazer_login(data):
    sid = request.sid
    cpf  = data.get("cpf",  "").strip()
    cnpj = data.get("cnpj", "").strip()
    senha = data.get("senha", "").strip()

    if not cpf or not cnpj or not senha:
        emit("erro_login", {"mensagem": "Preencha todos os campos obrigatórios."})
        return

    with _sessoes_lock:
        if sid in _sessoes_browser:
            emit("login_ok", {})
            return
        if not session_manager.pode_adicionar():
            emit("erro_sistema", {
                "mensagem": "Sistema com capacidade máxima (5 usuários simultâneos). "
                            "Tente novamente em alguns minutos."
            })
            return
        session_manager.adicionar(sid)

    threading.Thread(
        target=_executar_login,
        args=(sid, cpf, cnpj, senha),
        daemon=True,
    ).start()


@socketio.on("iniciar_doacao")
def handle_iniciar_doacao(data):
    sid = request.sid
    chaves    = data.get("chaves", [])
    cnpj_novo = data.get("cnpj", None)

    with _sessoes_lock:
        if sid not in _sessoes_browser:
            emit("erro_sistema", {"mensagem": "Sessão expirada. Faça login novamente."})
            return
        sessao = _sessoes_browser[sid]
        if cnpj_novo:
            sessao["cnpj_entidade"] = cnpj_novo
            sessao["cnpj_verificado"] = False

    threading.Thread(
        target=_executar_doacao,
        args=(sid, list(chaves)),
        daemon=True,
    ).start()


@socketio.on("encerrar_sessao")
def handle_encerrar():
    _fechar_sessao(request.sid)


@socketio.on("disconnect")
def handle_disconnect():
    _fechar_sessao(request.sid)


# ---------------------------------------------------------------------------
# Lógica em background
# ---------------------------------------------------------------------------

def _emit_safe(sid: str, evento: str, dados: dict) -> None:
    try:
        socketio.emit(evento, dados, to=sid)
    except Exception:
        pass


def _executar_login(sid: str, cpf: str, cnpj: str, senha: str) -> None:
    try:
        _emit_safe(sid, "status", {"mensagem": "Abrindo navegador..."})
        pw, browser, page = abrir_navegador(headless=True)

        _emit_safe(sid, "status", {"mensagem": "Realizando login no Nota Paraná..."})
        try:
            fazer_login_portal(page, cpf, senha)
        except CredenciaisInvalidasError:
            browser.close()
            pw.stop()
            session_manager.remover(sid)
            _emit_safe(sid, "erro_login", {"mensagem": "Usuário ou senha incorretos."})
            return

        with _sessoes_lock:
            _sessoes_browser[sid] = {
                "pw": pw,
                "browser": browser,
                "page": page,
                "cnpj_entidade": cnpj,
                "cnpj_verificado": False,
            }

        _emit_safe(sid, "login_ok", {})

    except Exception as exc:
        session_manager.remover(sid)
        _emit_safe(sid, "erro_sistema", {"mensagem": f"Erro ao iniciar sessão: {exc}"})


def _executar_doacao(sid: str, chaves: list[str]) -> None:
    with _sessoes_lock:
        if sid not in _sessoes_browser:
            _emit_safe(sid, "erro_sistema", {"mensagem": "Sessão expirada."})
            return
        sessao = _sessoes_browser[sid]

    page           = sessao["page"]
    cnpj_entidade  = sessao["cnpj_entidade"]
    verificar_cnpj = not sessao["cnpj_verificado"]

    def progresso_fn(info: dict) -> None:
        _emit_safe(sid, "progresso", info)

    try:
        _emit_safe(sid, "doacao_iniciada", {"total": len(chaves)})
        resultado = doar_lote(page, cnpj_entidade, chaves,
                              verificar_cnpj=verificar_cnpj,
                              progresso_fn=progresso_fn)

        if not resultado["cnpj_invalido"]:
            with _sessoes_lock:
                if sid in _sessoes_browser:
                    _sessoes_browser[sid]["cnpj_verificado"] = True

        _emit_safe(sid, "doacao_concluida", {
            "sucesso":               resultado["sucesso"],
            "erro":                  resultado["erro"],
            "erros_com_mensagem":    resultado["erros_com_mensagem"],
            "cnpj_invalido":         resultado["cnpj_invalido"],
            "parou_por_limite_erros": resultado["parou_por_limite_erros"],
        })

    except Exception as exc:
        _emit_safe(sid, "erro_sistema", {"mensagem": f"Erro durante doação: {exc}"})


def _fechar_sessao(sid: str) -> None:
    with _sessoes_lock:
        sessao = _sessoes_browser.pop(sid, None)
    session_manager.remover(sid)
    if sessao:
        threading.Thread(
            target=encerrar_sessao,
            args=(sessao["pw"], sessao["browser"], sessao["page"]),
            daemon=True,
        ).start()


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
