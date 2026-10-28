# =============================================================================
# install_toolchain.ps1
# Instala Git para Windows y MinGW-w64 (g++ y gdb) para MeriCode C++.
# Se ejecuta desde el instalador (con privilegios de administrador).
# =============================================================================

param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir
)

# Asegurar TLS 1.2 (PowerShell 5.1)
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

$ErrorActionPreference = 'Stop'

# --- URLs (actualizar si cambian) ---
$GitUrl      = 'https://github.com/git-for-windows/git/releases/download/v2.47.0.windows.1/Git-2.47.0-64-bit.exe'
$WinLibsRepo = 'brechtsanders/winlibs_mingw'

function Download-File {
    param([string]$Url, [string]$Out)
    if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
        & curl.exe -L --fail --retry 3 -o $Out $Url
        if ($LASTEXITCODE -ne 0) { throw "Error descargando: $Url" }
    }
    else {
        Invoke-WebRequest -Uri $Url -OutFile $Out -UseBasicParsing
    }
}

Write-Host ''
Write-Host '============================================================'
Write-Host '  Instalando herramientas: Git y MinGW-w64 (g++ / gdb)'
Write-Host '============================================================'
Write-Host ''

# --- 1) Git para Windows ---
Write-Host '[1/2] Instalando Git para Windows...'
$gitInstaller = Join-Path $env:TEMP 'git-installer.exe'
Download-File -Url $GitUrl -Out $gitInstaller
Start-Process -FilePath $gitInstaller -ArgumentList '/VERYSILENT','/NORESTART','/NOCANCEL','/SUPPRESSMSGBOXES' -Wait
Remove-Item $gitInstaller -Force -ErrorAction SilentlyContinue
Write-Host '      Git instalado.'
Write-Host ''

# --- 2) MinGW-w64 (winlibs): g++ y gdb ---
Write-Host '[2/2] Descargando MinGW-w64 (puede tardar varios minutos)...'
$release = Invoke-RestMethod -Uri "https://api.github.com/repos/$WinLibsRepo/releases/latest"
$asset = $release.assets |
    Where-Object { $_.name -match '^winlibs-x86_64-posix-seh-gcc-.*-mingw-w64ucrt-.*\.zip$' } |
    Select-Object -First 1
if (-not $asset) {
    $asset = $release.assets |
        Where-Object { $_.name -match '^winlibs-x86_64-posix-seh-gcc-.*\.zip$' } |
        Select-Object -First 1
}
if (-not $asset) { throw 'No se encontró un .zip de winlibs (x86_64 posix) en la última release.' }

Write-Host "      Descargando $($asset.name)..."
$zip = Join-Path $env:TEMP $asset.name
Download-File -Url $asset.browser_download_url -Out $zip

Write-Host '      Extrayendo...'
Expand-Archive -Path $zip -DestinationPath $InstallDir -Force
Remove-Item $zip -Force -ErrorAction SilentlyContinue

$gpp = Get-ChildItem -Path $InstallDir -Recurse -Filter 'g++.exe' | Select-Object -First 1
$gdb = Get-ChildItem -Path $InstallDir -Recurse -Filter 'gdb.exe'  | Select-Object -First 1
if (-not $gpp) { throw 'No se encontró g++.exe tras extraer winlibs.' }
if (-not $gdb) { throw 'No se encontró gdb.exe tras extraer winlibs.' }

$bin = $gpp.DirectoryName

# Añadir el directorio bin al PATH de la máquina (persistente)
$machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
if ($machinePath -notlike "*$bin*") {
    [Environment]::SetEnvironmentVariable('Path', "$machinePath;$bin", 'Machine')
    Write-Host "      PATH del sistema actualizado con: $bin"
}
else {
    Write-Host "      PATH ya contiene: $bin"
}

Write-Host ''
Write-Host '  Versiones detectadas:'
& (Join-Path $bin 'g++.exe') --version
& (Join-Path $bin 'gdb.exe') --version
Write-Host ''
Write-Host '  Instalación de herramientas completada correctamente.'
