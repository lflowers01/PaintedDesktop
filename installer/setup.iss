; Inno Setup script for Daily Art Wallpaper
; This script creates a Windows installer for the application

#define MyAppName "Daily Art Wallpaper"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Daily Art Wallpaper"
#define MyAppExeName "DailyArtWallpaper.exe"
#define MyAppAssocName MyAppName + " App"
#define MyAppAssocExt ".daw"
#define MyAppAssocProgId "DailyArtWallpaper.1"
#define BuildOutputDir "dist\DailyArtWallpaper"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{12345678-1234-1234-1234-123456789012}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
; Uncomment the following line to run the post install step when Run checkbox is checked.
PostInstallRunCheck=idYes
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=dist
OutputBaseFilename=DailyArtWallpaperSetup

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "startup"; Description: "Launch Daily Art Wallpaper at Windows startup"; GroupDescription: "Startup Options"; Flags: unchecked

[Files]
Source: "{#BuildOutputDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BuildOutputDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autopf}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; Register for startup if task is selected
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: "{app}\{#MyAppExeName}"; Tasks: startup; Flags: uninsdeletevalue

[Code]
// Check if running on Windows
function InitializeSetup(): Boolean;
begin
  if not IsWin32Compatible then
  begin
    MsgBox('This application requires Windows XP or later.', mbInformation, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;

// Ensure the app directory is created before installation
procedure InitializeWizard();
begin
  // Nothing special needed here
end;

// After installation, optionally register for startup
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // The registry entry is handled by the [Registry] section
  end;
end;
