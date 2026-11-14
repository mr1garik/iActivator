; Windows installer for iActivator (Inno Setup 6.3 or newer).
; Built by the GitHub workflow after `python build.py`:
;   iscc /DAppVersion=3.0.1 installer\iActivator.iss
; Output: dist\iActivator-windows-setup.exe
;
; Installs for the current user only (%LOCALAPPDATA%\Programs\iActivator), so neither the
; installation nor the in-app updates ask for administrator rights. History, settings and
; logs live in %APPDATA%\iActivator and are not touched by installing, updating or removing.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{9B4A6E2C-3F1D-4C8E-A7B5-6D2E1F0C9A31}
AppName=iActivator
AppVersion={#AppVersion}
AppVerName=iActivator {#AppVersion}
AppPublisher=mr1garik
AppPublisherURL=https://github.com/mr1garik/iActivator
AppSupportURL=https://github.com/mr1garik/iActivator/issues
AppUpdatesURL=https://github.com/mr1garik/iActivator/releases
VersionInfoVersion={#AppVersion}
DefaultDirName={autopf}\iActivator
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist
OutputBaseFilename=iActivator-windows-setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\iActivator.exe
UninstallDisplayName=iActivator
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; The app is closed by the in-app updater before this runs; this covers a manual install
; while it is still open (it may sit in the tray).
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
; Library files of the previous version; the new ones are copied right after.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "..\dist\iActivator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\iActivator"; Filename: "{app}\iActivator.exe"
Name: "{autodesktop}\iActivator"; Filename: "{app}\iActivator.exe"; Tasks: desktopicon

[Run]
; After a normal install: a "Launch iActivator" checkbox on the last page.
Filename: "{app}\iActivator.exe"; Description: "{cm:LaunchProgram,iActivator}"; Flags: nowait postinstall skipifsilent
; After a silent in-app update: start the app again.
Filename: "{app}\iActivator.exe"; Flags: nowait skipifnotsilent
