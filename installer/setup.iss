; NGOKAF TRANS — Inno Setup 6 installer script
; Output: installer\Output\Setup_Ngokaf_Trans.exe

#define MyAppName "NGOKAF TRANS"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "NGOKAF"
#define MyAppExeName "NGOKAF_TRANS.exe"

[Setup]
AppId=NGOKAF.TRANS.Desktop.2026
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt
OutputDir=Output
OutputBaseFilename=Setup_Ngokaf_Trans
SetupIconFile=..\assets\icons\ngokaf.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
VersionInfoVersion=2.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Full PyInstaller onedir package
Source: "..\dist\NGOKAF_TRANS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Seed user config only on first install (never overwrite existing)
Source: "..\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist
Source: "..\config.ini.example"; DestDir: "{app}"; DestName: "config.ini"; Flags: onlyifdoesntexist
Source: "..\.env.example"; DestDir: "{app}"; DestName: ".env.example"; Flags: ignoreversion
Source: "..\config.ini.example"; DestDir: "{app}"; DestName: "config.ini.example"; Flags: ignoreversion

[Dirs]
Name: "{app}\logs"
Name: "{app}\backups"; Flags: uninsneveruninstall
Name: "{app}\reports"
Name: "{app}\temp"
Name: "{app}\config"
Name: "{app}\assets"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\temp"
Type: filesandordirs; Name: "{app}\reports"
Type: filesandordirs; Name: "{app}\config"
Type: filesandordirs; Name: "{app}\assets"
Type: files; Name: "{app}\.env"
Type: files; Name: "{app}\config.ini"

[Code]
var
  KeepBackups: Boolean;

function InitializeUninstall(): Boolean;
begin
  KeepBackups := False;
  if DirExists(ExpandConstant('{app}\backups')) then
  begin
    if MsgBox('Souhaitez-vous conserver les sauvegardes MySQL (dossier backups) ?',
              mbConfirmation, MB_YESNO) = IDYES then
      KeepBackups := True;
  end;
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if not KeepBackups then
    begin
      DelTree(ExpandConstant('{app}\backups'), True, True, True);
      DelTree(ExpandConstant('{app}'), True, True, True);
    end;
  end;
end;
