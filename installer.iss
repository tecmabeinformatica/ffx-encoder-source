#define MyAppName "FFX Encoder GUI"
#define MyAppVersion "2.0.0"
#define MyAppDisplayVersion "2.0 Final"
#define MyAppPublisher "Tecmabe Informática"
#define MyAppExeName "FFX Encoder GUI.exe"

[Setup]
AppId={{F2253A7E-D146-4CB7-A6DD-342068F46CE6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppDisplayVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName=C:\FFX Encoder GUI
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=release
OutputBaseFilename=FFX Encoder GUI 2.0 Final Instalador
SetupIconFile=icone.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
WizardStyle=modern
Compression=lzma2/ultra64
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
ChangesAssociations=yes
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Instalador do {#MyAppName}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked
Name: "contextmenu"; Description: "Adicionar “Abrir com FFX Encoder GUI” ao menu de contexto de pastas"; GroupDescription: "Integração com o Windows:"; Flags: checkedonce

[Files]
Source: "dist\FFX Encoder GUI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
Root: HKLM; Subkey: "Software\Classes\Directory\Background\shell\FFX Encoder GUI"; ValueType: string; ValueName: ""; ValueData: "Abrir com FFX Encoder GUI"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Classes\Directory\Background\shell\FFX Encoder GUI"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName}"; Tasks: contextmenu
Root: HKLM; Subkey: "Software\Classes\Directory\Background\shell\FFX Encoder GUI\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%V"""; Tasks: contextmenu
Root: HKLM; Subkey: "Software\Classes\Directory\shell\FFX Encoder GUI"; ValueType: string; ValueName: ""; ValueData: "Abrir com FFX Encoder GUI"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\Classes\Directory\shell\FFX Encoder GUI"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName}"; Tasks: contextmenu
Root: HKLM; Subkey: "Software\Classes\Directory\shell\FFX Encoder GUI\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

[InstallDelete]
Type: files; Name: "{app}\ffx.dat"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    { Remove o registro criado pelo instalador Python antigo. }
    RegDeleteKeyIncludingSubkeys(HKCU,
      'Software\Microsoft\Windows\CurrentVersion\Uninstall\FFX Encoder GUI');
    RegDeleteKeyIncludingSubkeys(HKCU,
      'Software\Classes\Directory\Background\shell\FFX Encoder GUI');
    RegDeleteKeyIncludingSubkeys(HKCU,
      'Software\Classes\Directory\shell\FFX Encoder GUI');
  end;
end;
