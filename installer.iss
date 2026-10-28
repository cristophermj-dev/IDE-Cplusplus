; =============================================================================
; MeriCode C++ - Script de instalación para Windows (Inno Setup 6)
; =============================================================================
; Requiere: Inno Setup 6  ->  https://jrsoftware.org/isinfo.php
; Antes de compilar, genera dist\MeriCode.exe con build_windows.bat.
; El instalador resultante (dist\MeriCode-Setup.exe) instalará el IDE y,
; durante la instalación, descargará e instalará automáticamente:
;   - Git para Windows
;   - MinGW-w64 (g++ y gdb)
; y los añadirá al PATH del sistema.
; =============================================================================

#define MyAppName "MeriCode C++"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "MERIMAD"
#define MyAppExeName "MeriCode.exe"

[Setup]
AppId={{7B2A3F1D-9C4E-4A8B-B6D2-1E5F8C3A9D07}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\MeriCode
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=MeriCode-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
ChangesEnvironment=yes
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "install_toolchain.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar MeriCode"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; \
    Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\install_toolchain.ps1"" -InstallDir ""{app}"""; \
    StatusMsg: "Descargando e instalando el compilador (MinGW-w64: g++/gdb) y Git..."; \
    Flags: waituntilterminated
