; Inno Setup Script for 酒店影像控制系統
; Requires Inno Setup 6.x

[Setup]
AppName=酒店影像控制系統
AppVersion=1.0.0
AppPublisher=Jiudian
DefaultDirName={autopf}\JiudianVideoControl
DefaultGroupName=酒店影像控制系統
OutputDir=output
OutputBaseFilename=JiudianVideoControl_Setup_1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\JiudianVideoControl.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\酒店影像控制系統"; Filename: "{app}\JiudianVideoControl.exe"
Name: "{group}\解除安裝"; Filename: "{uninstallexe}"
Name: "{autodesktop}\酒店影像控制系統"; Filename: "{app}\JiudianVideoControl.exe"

[Run]
Filename: "{app}\JiudianVideoControl.exe"; Description: "啟動酒店影像控制系統"; Flags: nowait postinstall skipifsilent
