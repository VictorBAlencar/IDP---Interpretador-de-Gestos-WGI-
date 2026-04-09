[Setup]
AppName=WGC Backend
AppVersion=1.0
DefaultDirName={autopf}\WGC Backend
DefaultGroupName=WGC
OutputDir=Output
OutputBaseFilename=WGC_Backend_Installer
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes

[Files]
Source: "dist\wgc\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\WGC Backend"; Filename: "{app}\wgc.exe"
Name: "{autodesktop}\WGC Backend"; Filename: "{app}\wgc.exe"

[Run]
Filename: "{app}\wgc.exe"; Description: "Iniciar Motor de Gestos WGC"; Flags: nowait postinstall skipifsilent