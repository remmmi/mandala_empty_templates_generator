; Inno Setup Script for Mandala PDF Generator
; This script creates a Windows installer for the application
; Version number is passed via command line: /DAppVersion=x.y.z

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

#define AppName "Mandala PDF Generator"
#define AppExeName "Mandala PDF Generator.exe"
#define AppPublisher "remmmi"
#define AppURL "https://github.com/remmmi/mandala_empty_templates_generator"

[Setup]
; Application identity
AppId={{8F3D2C1A-9B4E-4F7C-A2D5-6E8B9C1D3F5A}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}

; Output configuration
OutputDir=installer_output
OutputBaseFilename=Mandala-PDF-Generator-Setup-v{#AppVersion}
Compression=lzma2/max
SolidCompression=yes

; Installer UI
WizardStyle=modern
DisableWelcomePage=no
LicenseFile=LICENSE

; Privileges
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Uninstall
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable (from PyInstaller build)
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
; Configuration examples (zoo directory)
Source: "zoo\*"; DestDir: "{app}\zoo"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start menu icon
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
; Desktop icon (optional)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Option to launch after installation
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
