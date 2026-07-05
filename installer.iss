; installer.iss
; Instalador PDV DinDin Show — gerado automaticamente

#define AppName      "PDV DinDin Show"
#define AppVersion   "1.0.0"
#define AppPublisher "DinDin Show"
#define AppURL       ""
#define InstallDir   "{autopf}\PDV_DinDin_Show"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
DefaultDirName={#InstallDir}
DefaultGroupName={#AppName}
OutputDir=dist\installer
OutputBaseFilename=PDV_DinDin_Show_Setup_v{#AppVersion}
SetupIconFile=assets\Logojamir.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=
; Antes de instalar, mostra aviso sobre o driver da impressora
InfoBeforeFile=

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon_totem"; Description: "Criar atalho do Totem na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: checkedonce
Name: "desktopicon_admin"; Description: "Criar atalho do Admin na Área de Trabalho"; GroupDescription: "Atalhos:"; Flags: checkedonce
Name: "startuptotem"; Description: "Iniciar Totem automaticamente com o Windows"; GroupDescription: "Inicialização:"; Flags: unchecked

[Files]
; --- Totem (inclui o servidor API) ---
Source: "dist\PDV_Totem\*"; DestDir: "{app}\PDV_Totem"; Flags: ignoreversion recursesubdirs createallsubdirs

; --- Admin ---
Source: "dist\PDV_Admin\*"; DestDir: "{app}\PDV_Admin"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Menu Iniciar
Name: "{group}\Totem (Tela do Cliente)"; Filename: "{app}\PDV_Totem\PDV_Totem.exe"; WorkingDir: "{app}\PDV_Totem"
Name: "{group}\Painel Administrativo";   Filename: "{app}\PDV_Admin\PDV_Admin.exe";  WorkingDir: "{app}\PDV_Admin"
Name: "{group}\Desinstalar {#AppName}";  Filename: "{uninstallexe}"

; Área de Trabalho (opcional)
Name: "{autodesktop}\PDV Totem";         Filename: "{app}\PDV_Totem\PDV_Totem.exe"; WorkingDir: "{app}\PDV_Totem"; Tasks: desktopicon_totem
Name: "{autodesktop}\PDV Admin";         Filename: "{app}\PDV_Admin\PDV_Admin.exe";  WorkingDir: "{app}\PDV_Admin"; Tasks: desktopicon_admin

; Inicialização automática com o Windows (opcional)
Name: "{userstartup}\PDV Totem";         Filename: "{app}\PDV_Totem\PDV_Totem.exe"; WorkingDir: "{app}\PDV_Totem"; Tasks: startuptotem

[Run]
; Abrir o Totem ao finalizar a instalação
Filename: "{app}\PDV_Totem\PDV_Totem.exe"; WorkingDir: "{app}\PDV_Totem"; Description: "Abrir o Totem agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove o banco de dados ao desinstalar (opcional — comente se quiser manter os dados)
; Type: files; Name: "{app}\pdv_jamir.db"
