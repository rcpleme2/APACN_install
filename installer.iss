; installer.iss
; -------------
; Script Inno Setup para gerar o instalador Windows do APACN – Nota Paraná.
;
; Pré-requisito: Inno Setup 6+ instalado em C:\Program Files (x86)\Inno Setup 6\
; Download: https://jrsoftware.org/isdl.php
;
; Este script deve ser executado DEPOIS do PyInstaller gerar dist\APACN\.

#define AppName      "APACN - Nota Paraná"
#define AppVersion   "1.0"
#define AppPublisher "APACN"
#define AppExeName   "APACN.exe"
#define SourceDir    "dist\APACN"

[Setup]
AppId={{B7C2A3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=
DefaultDirName={autopf}\APACN
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=APACN_Setup_v{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Exige Windows 10 ou superior (necessário para Playwright/Chromium)
MinVersion=10.0
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; \
  Description: "Criar atalho na Área de Trabalho"; \
  GroupDescription: "Ícones adicionais:"; \
  Flags: unchecked

[Files]
; Copia todo o conteúdo gerado pelo PyInstaller
Source: "{#SourceDir}\*"; \
  DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";        Filename: "{app}\{#AppExeName}"
Name: "{group}\Desinstalar APACN"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; \
  Filename: "{app}\{#AppExeName}"; \
  Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; \
  Description: "Iniciar {#AppName} agora"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove o arquivo de configuração local gerado em execução
Type: files; Name: "{app}\config.json"

[Messages]
; Mensagens personalizadas em português
WelcomeLabel1=Bem-vindo ao instalador do {#AppName}
WelcomeLabel2=Este assistente irá instalar o {#AppName} no seu computador.%n%nRecomenda-se fechar todos os outros aplicativos antes de continuar.
FinishedHeadingLabel=Instalação concluída!
FinishedLabel=O {#AppName} foi instalado com sucesso.%n%nClique em Concluir para fechar o instalador.
