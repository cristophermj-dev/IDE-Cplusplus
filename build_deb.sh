#!/usr/bin/env bash
# =============================================================================
# build_deb.sh - Construye el paquete .deb de MeriCode C++ (instalable en Ubuntu)
#
# Uso:   bash build_deb.sh
# Salida: mericode-cpp_<version>_all.deb en el directorio padre del proyecto.
#
# Las dependencias g++, git y gdb van en "Depends" para que, al instalar con
# `apt install ./mericode-cpp_*.deb`, se instalen automáticamente si faltan.
# =============================================================================
set -euo pipefail

# --- Configuración del paquete ---
PKG_NAME="mericode-cpp"
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
mkdir -p "${PKG_ROOT}/usr/share/icons/hicolor/scalable/apps"
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
Depends: python3, python3-tk, g++, git, gdb
Installed-Size: PLACEHOLDER
Description: MeriCode C++ - IDE para programar en C++
 MeriCode C++ es un IDE completo para programar en C++,
 desarrollado en Python con Tkinter, con interfaz gráfica
 moderna en tema oscuro.
 .
 Incluye editor con resaltado de sintaxis C++, autocompletado,
 números de línea, múltiples pestañas, compilación y ejecución
 con g++/clang++, depuración con GDB, gestión de proyectos y
 sincronización con GitHub.
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
cat > "${PKG_ROOT}/usr/bin/mericode" <<'LAUNCHER'
#!/bin/sh
# MeriCode C++ - Lanzador de la aplicación.
exec /usr/bin/python3 /usr/lib/mericode-cpp/main.py "$@"
LAUNCHER

# --- 7. Entrada del menú de aplicaciones ---
cat > "${PKG_ROOT}/usr/share/applications/mericode.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=MeriCode C++
GenericName=IDE C++
Comment=IDE completo para programar en C++
Exec=mericode %F
Icon=mericode
Terminal=false
Categories=Development;IDE;
Keywords=IDE;C++;Editor;Compilador;Debugger;
StartupNotify=true
MimeType=text/x-c++src;text/x-c++hdr;text/plain;
DESKTOP

# --- 8. Icono SVG ---
cat > "${PKG_ROOT}/usr/share/icons/hicolor/scalable/apps/mericode.svg" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e2a4a"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect x="8" y="8" width="240" height="240" rx="48" fill="url(#bg)"/>
  <rect x="8" y="8" width="240" height="240" rx="48" fill="none" stroke="#3b82f6" stroke-width="6"/>
  <text x="128" y="170" font-family="DejaVu Sans, sans-serif" font-size="96" font-weight="bold" fill="#ffffff" text-anchor="middle">C++</text>
</svg>
SVG

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
chmod 0755 "${PKG_ROOT}/usr/bin/mericode" "${PKG_ROOT}/DEBIAN/postinst"

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
