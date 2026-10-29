#!/usr/bin/env bash
# =============================================================================
# build_deb.sh - Construye el paquete .deb de DevQbo (instalable en Ubuntu)
#
# Uso:   bash build_deb.sh
# Salida: devqbo_<version>_all.deb en el directorio padre del proyecto.
#
# Las dependencias g++, git y gdb van en "Depends" para que, al instalar con
# `apt install ./devqbo_*.deb`, se instalen automáticamente si faltan.
# =============================================================================
set -euo pipefail

# --- Configuración del paquete ---
PKG_NAME="devqbo"
VERSION="1.0.0"
ARCH="all"
MAINTAINER="MSc. Cristopher Montero Jiménez <cristopher.montero.jimenez@una.ac.cr>"

# --- Rutas ---
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="$(cd "${PROJECT_DIR}/.." && pwd)"
BUILD_DIR="$(mktemp -d)"
PKG_ROOT="${BUILD_DIR}/${PKG_NAME}_${VERSION}_${ARCH}"

cleanup() { rm -rf "${BUILD_DIR}"; }
trap cleanup EXIT

# --- 1. Estructura de directorios ---
mkdir -p "${PKG_ROOT}/DEBIAN"
mkdir -p "${PKG_ROOT}/usr/lib/${PKG_NAME}"
mkdir -p "${PKG_ROOT}/usr/bin"
mkdir -p "${PKG_ROOT}/usr/share/applications"
mkdir -p "${PKG_ROOT}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${PKG_ROOT}/usr/share/doc/${PKG_NAME}"

# --- 2. Copiar el código fuente (sin bytecode .pyc) ---
cp "${PROJECT_DIR}/main.py" "${PKG_ROOT}/usr/lib/${PKG_NAME}/"
cp -r "${PROJECT_DIR}/ide" "${PKG_ROOT}/usr/lib/${PKG_NAME}/"
find "${PKG_ROOT}" -type d -name __pycache__ -prune -exec rm -rf {} +

# --- 3. Documentación ---
cp "${PROJECT_DIR}/LICENSE" "${PKG_ROOT}/usr/share/doc/${PKG_NAME}/copyright"
cp "${PROJECT_DIR}/README.md" "${PKG_ROOT}/usr/share/doc/${PKG_NAME}/README"

# --- 4. Archivo de control de Debian ---
cat > "${PKG_ROOT}/DEBIAN/control" <<CONTROL
Package: ${PKG_NAME}
Version: ${VERSION}
Section: devel
Priority: optional
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Depends: python3, python3-tk, g++, git, gdb, python3-pil, python3-reportlab
Installed-Size: PLACEHOLDER
Description: DevQbo - IDE para programar en C++
 DevQbo es un IDE completo para programar en C++,
 desarrollado en Python con Tkinter, con interfaz gráfica
 moderna en tema oscuro.
 .
 Incluye editor con resaltado de sintaxis C++, autocompletado,
 números de línea, múltiples pestañas, compilación y ejecución
 con g++/clang++, depuración con GDB, gestión de proyectos,
 sincronización con GitHub y editor de diagramas UML con
 guardado en XML y exportación a PNG/PDF.
CONTROL

# --- 5. Script de post-instalación ---
cat > "${PKG_ROOT}/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e

# Actualizar las bases de datos del escritorio si existen las herramientas.
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi

exit 0
POSTINST

# --- 6. Lanzador en /usr/bin ---
cat > "${PKG_ROOT}/usr/bin/devqbo" <<'LAUNCHER'
#!/bin/sh
# DevQbo - Lanzador de la aplicación.
exec /usr/bin/python3 /usr/lib/devqbo/main.py "$@"
LAUNCHER

# --- 7. Entrada del menú de aplicaciones ---
cat > "${PKG_ROOT}/usr/share/applications/devqbo.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=DevQbo
GenericName=IDE C++
Comment=IDE completo para programar en C++
Exec=devqbo %F
Icon=devqbo
Terminal=false
Categories=Development;IDE;
Keywords=IDE;C++;Editor;Compilador;Debugger;
StartupNotify=true
MimeType=text/x-c++src;text/x-c++hdr;text/plain;
DESKTOP

# --- 8. Icono de la aplicación (logo del gato DevQbo) ---
cp "${PROJECT_DIR}/ide/assets/icon.png" \
   "${PKG_ROOT}/usr/share/icons/hicolor/256x256/apps/devqbo.png"

# --- 9. Changelog (política Debian) ---
cat > "${PKG_ROOT}/usr/share/doc/${PKG_NAME}/changelog" <<CHANGELOG
${PKG_NAME} (${VERSION}) stable; urgency=medium

  * Paquete .deb para Ubuntu/Debian con dependencias automáticas
    (python3, python3-tk, g++, git y gdb).

 -- ${MAINTAINER}  $(LC_ALL=C date -R)
CHANGELOG

# --- 10. Permisos estándar ---
find "${PKG_ROOT}" -type d -exec chmod 0755 {} +
find "${PKG_ROOT}" -type f -exec chmod 0644 {} +
chmod 0755 "${PKG_ROOT}/usr/bin/devqbo" "${PKG_ROOT}/DEBIAN/postinst"

# --- 11. Comprimir changelog ---
gzip -9 -n -f "${PKG_ROOT}/usr/share/doc/${PKG_NAME}/changelog"

# --- 12. Tamaño instalado (KiB) ---
SIZE=$(du -sk "${PKG_ROOT}/usr" | cut -f1)
sed -i "s/^Installed-Size: .*/Installed-Size: ${SIZE}/" "${PKG_ROOT}/DEBIAN/control"

# --- 13. Construir el .deb ---
OUT="${OUT_DIR}/${PKG_NAME}_${VERSION}_${ARCH}.deb"
rm -f "${OUT}"
dpkg-deb --build --root-owner-group "${PKG_ROOT}" "${OUT}"

echo ""
echo "======================================================"
echo " Paquete generado correctamente:"
echo "   ${OUT}"
echo "======================================================"
echo ""
dpkg-deb --info "${OUT}"
