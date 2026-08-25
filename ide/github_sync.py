"""
Sincronización con GitHub para MeriCode C++.

Este módulo permite publicar un proyecto en GitHub y mantenerlo
sincronizado (push / pull). Usa:

- git (a través de subprocess) para las operaciones de repositorio
  local y remoto.
- La GitHub REST API (con urllib de la librería estándar, sin
  dependencias externas) para validar el token y crear repositorios.

Seguridad:
El token (Personal Access Token) se guarda en ~/.mericode/github.json,
fuera del proyecto, y para las operaciones autenticadas se inyecta por
variables de entorno en cada invocación de git, de modo que el token
NO queda escrito en .git/config ni en archivos versionados.
"""

import os
import json
import base64
import subprocess
import urllib.request
import urllib.parse

# --- Constantes de configuración global (por usuario) ---
HOME = os.path.expanduser("~")
CONFIG_DIR = os.path.join(HOME, ".mericode")
CONFIG_FILE = os.path.join(CONFIG_DIR, "github.json")

# URL base de la GitHub REST API
GITHUB_API = "https://api.github.com"
GITHUB_HTTPS = "https://github.com"


class GitHubError(Exception):
    """Excepción genérica de la sincronización con GitHub."""


def _run(cmd, cwd=None, env=None, check=True):
    """Ejecuta un comando externo y devuelve su salida combinada.

    Args:
        cmd: Lista de argumentos del comando.
        cwd: Directorio de trabajo del comando (opcional).
        env: Variables de entorno adicionales (opcional).
        check: Si True, lanza GitHubError cuando el código de salida != 0.

    Returns:
        str: Salida estándar + salida de error del comando.

    Raises:
        GitHubError: Si el comando falla (cuando check=True).
    """
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=full_env,
        capture_output=True,
        text=True,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    output = output.strip()
    if check and proc.returncode != 0:
        raise GitHubError(output or f"El comando falló: {' '.join(cmd)}")
    return output


def _auth_env(token):
    """Construye el entorno con la cabecera de autorización de git.

    Se configura GIT_CONFIG_* para inyectar un Authorization header
    sin escribir el token en ningún archivo de configuración.
    """
    # Basic con usuario arbitrario 'x-access-token' y contraseña = token.
    credentials = base64.b64encode(
        ("x-access-token:" + token).encode("utf-8")
    ).decode("ascii")
    env = {
        # Evita que git intente interactuar (mensajes de prompt).
        "GIT_TERMINAL_PROMPT": "0",
        # Inyecta la cabecera de autorización para github.com.
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
        "GIT_CONFIG_VALUE_0": "Authorization: Basic " + credentials,
    }
    return env


class GitHubSync:
    """Gestor de sincronización con GitHub.

    Se encarga de la configuración global (token, dueño, repositorio),
    las operaciones con git y la creación de repositorios en GitHub.
    """

    def __init__(self):
        self._config = None

    # ------------------------------------------------------------------
    # Configuración global (~/.mericode/github.json)
    # ------------------------------------------------------------------

    def load_config(self):
        """Carga la configuración global guardada en disco.

        Returns:
            dict: Configuración (token, owner, repo, private).
        """
        if self._config is not None:
            return self._config
        cfg = {"token": "", "owner": "", "repo": "", "private": False}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                cfg.update({k: saved.get(k, cfg[k]) for k in cfg})
            except (OSError, ValueError):
                pass
        self._config = cfg
        return cfg

    def save_config(self, cfg=None):
        """Guarda la configuración global en disco.

        Args:
            cfg: Configuración a guardar (si es None se guarda la actual).
        """
        if cfg is None:
            cfg = self.load_config()
        self._config = cfg
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        # Restringir permisos del archivo (contiene un token).
        try:
            os.chmod(CONFIG_FILE, 0o600)
        except OSError:
            pass

    def set_credentials(self, token, owner=None, repo=None, private=None):
        """Actualiza las credenciales guardadas de forma persistente.

        Args:
            token: Personal Access Token de GitHub.
            owner: Usuario/organización propietario del repositorio.
            repo: Nombre del repositorio.
            private: True si el repositorio debe ser privado.
        """
        cfg = self.load_config()
        cfg["token"] = (token or "").strip()
        if owner is not None:
            cfg["owner"] = owner.strip()
        if repo is not None:
            cfg["repo"] = repo.strip()
        if private is not None:
            cfg["private"] = bool(private)
        self.save_config(cfg)
        return cfg

    def has_token(self):
        """Indica si existen credenciales configuradas."""
        cfg = self.load_config()
        return bool(cfg.get("token"))
# ------------------------------------------------------------------
    # GitHub REST API
    # ------------------------------------------------------------------

    def _api_request(self, token, method, url, payload=None):
        """Realiza una petición a la GitHub REST API.

        Args:
            token: Personal Access Token.
            method: Método HTTP (GET, POST...).
            url: URL completa de la petición.
            payload: Diccionario a enviar como JSON (opcional).

        Returns:
            dict: Respuesta JSON de la API.

        Raises:
            GitHubError: Si la API devuelve un error.
        """
        headers = {
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "User-Agent": "MeriCode-Cplusplus",
        }
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                if not body:
                    return {}
                return json.loads(body)
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", errors="replace")
            code = e.code
            if code == 401:
                raise GitHubError(
                    "Token inválido o sin permisos (HTTP 401). Verifica tu "
                    "Personal Access Token."
                )
            if code == 403:
                raise GitHubError(
                    "Acceso denegado (HTTP 403). El token no tiene permisos "
                    "para esta acción o se alcanzó el límite de peticiones."
                )
            if code == 404:
                raise GitHubError(
                    "Recurso no encontrado (HTTP 404). Verifica el nombre del "
                    "repositorio y el dueño."
                )
            raise GitHubError(f"Error de la API de GitHub (HTTP {code}): {msg}")
        except urllib.error.URLError as e:
            raise GitHubError(
                "No se pudo conectar con GitHub. Verifica tu conexión a Internet: "
                f"{e.reason}"
            )

    def get_authenticated_user(self, token):
        """Devuelve el login del usuario autenticado con el token.

        Returns:
            str: Login (nombre de usuario) de GitHub.
        """
        data = self._api_request(token, "GET", GITHUB_API + "/user")
        return data.get("login", "")

    def repo_exists(self, token, owner, repo):
        """Indica si existe un repositorio en GitHub.

        Returns:
            bool: True si el repositorio existe.
        """
        url = (
            f"{GITHUB_API}/repos/"
            f"{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}"
        )
        try:
            self._api_request(token, "GET", url)
            return True
        except GitHubError as e:
            if "404" in str(e):
                return False
            raise

    def create_repo(self, token, name, private=False, description=""):
        """Crea un repositorio bajo el usuario autenticado.

        Args:
            token: Personal Access Token.
            name: Nombre del repositorio.
            private: True para crearlo privado.
            description: Descripción opcional del repositorio.

        Returns:
            dict: Datos del repositorio creado.
        """
        payload = {
            "name": name,
            "private": bool(private),
            "description": description,
            "auto_init": False,
            "license_template": None,
        }
        return self._api_request(token, "POST", GITHUB_API + "/user/repos", payload)
# ------------------------------------------------------------------
    # Operaciones con git
    # ------------------------------------------------------------------

    def is_repo(self, project_path):
        """Indica si el directorio del proyecto ya es un repositorio git."""
        return os.path.isdir(os.path.join(project_path, ".git"))

    def ensure_repo(self, project_path):
        """Inicializa el repositorio git si el proyecto aún no es uno.

        Además asigna un usuario local (name/email) si no existe, para
        que el primer commit no falle.
        """
        if not self.is_repo(project_path):
            _run(["git", "init"], cwd=project_path)
        # Asegurar un usuario local para poder hacer commits.
        try:
            name = _run(["git", "config", "user.name"], cwd=project_path, check=False)
        except GitHubError:
            name = ""
        if not name:
            cfg = self.load_config()
            user = cfg.get("owner") or "MeriCode User"
            _run(["git", "config", "user.name", user], cwd=project_path)
            email = cfg.get("owner", "") or "mericode"
            _run(
                ["git", "config", "user.email", f"{email}@users.noreply.github.com"],
                cwd=project_path,
            )

    def current_branch(self, project_path):
        """Devuelve la rama actual del repositorio.

        Returns:
            str: Nombre de la rama actual (o '' si no hay ninguna).
        """
        try:
            return _run(["git", "branch", "--show-current"], cwd=project_path)
        except GitHubError:
            return ""

    def create_gitignore(self, project_path):
        """Crea un .gitignore por defecto si no existe.

        Evita versionar artefactos de compilación.
        """
        gitignore = os.path.join(project_path, ".gitignore")
        if os.path.exists(gitignore):
            return
        content = (
            "# Sobres eliminados por MeriCode (auto-generado)\n"
            "build/\nbin/\nobj/\n*.o\n*.obj\n*.exe\n*.out\n*.class\n"
            "*.pyc\n__pycache__/\n.vs/\n.idea/\n*.cmj.save\n"
        )
        with open(gitignore, "w", encoding="utf-8") as f:
            f.write(content)

    def set_remote(self, project_path, owner, repo):
        """Configura el remoto 'origin' con la URL pública (sin token)."""
        url = (
            f"{GITHUB_HTTPS}/{urllib.parse.quote(owner)}/"
            f"{urllib.parse.quote(repo)}.git"
        )
        remotes = _run(["git", "remote"], cwd=project_path, check=False)
        names = set(remotes.split())
        if "origin" in names:
            _run(["git", "remote", "set-url", "origin", url], cwd=project_path)
        else:
            _run(["git", "remote", "add", "origin", url], cwd=project_path)
        return url

    def remote_url(self, project_path):
        """Devuelve la URL del remoto 'origin' o una cadena vacía.

        Devuelve '' si no existe el remoto o si no es un repositorio git.
        """
        if not self.is_repo(project_path):
            return ""
        out = _run(
            ["git", "remote", "get-url", "origin"],
            cwd=project_path,
            check=False,
        )
        if not out or out.lower().startswith(("error", "fatal")):
            return ""
        return out

    def status(self, project_path):
        """Devuelve el estado del repositorio (git status)."""
        branch = self.current_branch(project_path) or "(sin commits todavía)"
        status = _run(["git", "status", "--short"], cwd=project_path, check=False)
        remote = self.remote_url(project_path)
        lines = [
            f"Repositorio git: {'sí' if self.is_repo(project_path) else 'no'}",
            f"Rama actual: {branch}",
            f"Remoto origin: {remote or 'no configurado'}",
            "",
            "Archivos modificados/pendientes:",
        ]
        lines.append(status if status else "  (sin cambios pendientes)")
        return "\n".join(lines)

    def commit(self, project_path, message):
        """Agrega todos los cambios y crea un commit.

        Args:
            project_path: Directorio del proyecto.
            message: Mensaje del commit.

        Returns:
            str: Salida de git add/commit (puede avisar de que no hay cambios).
        """
        if not self.is_repo(project_path):
            self.ensure_repo(project_path)
        _run(["git", "add", "-A"], cwd=project_path)
        return _run(["git", "commit", "-m", message], cwd=project_path, check=False)

    def push(self, project_path, token, owner, repo, branch):
        """Sube la rama actual al repositorio remoto.

        La autenticación se inyecta por entorno (no se guarda el token).

        Returns:
            str: Salida de git push.
        """
        url = (
            f"{GITHUB_HTTPS}/{urllib.parse.quote(owner)}/"
            f"{urllib.parse.quote(repo)}.git"
        )
        env = _auth_env(token)
        return _run(
            ["git", "push", url, f"HEAD:{branch}"],
            cwd=project_path,
            env=env,
        )

    def pull(self, project_path, token, owner, repo, branch):
        """Descarga y fusiona los cambios del repositorio remoto.

        Returns:
            str: Salida de git pull.
        """
        url = (
            f"{GITHUB_HTTPS}/{urllib.parse.quote(owner)}/"
            f"{urllib.parse.quote(repo)}.git"
        )
        env = _auth_env(token)
        try:
            out = _run(["git", "pull", url, branch], cwd=project_path, env=env)
        except GitHubError:
            # Reintenta con rebase por si las ramas no tienen historial común.
            out = _run(
                ["git", "pull", "--rebase", url, branch],
                cwd=project_path,
                env=env,
            )
        # Restablecer el remoto a su URL limpia por si algo la cambió.
        out += "\n" + self.set_remote(project_path, owner, repo)
        return out
# ------------------------------------------------------------------
    # Acciones compuestas
    # ------------------------------------------------------------------

    def publish(self, project_path, token, owner, repo, private, message):
        """Publica el proyecto por primera vez en GitHub.

        Inicializa el repo, crea el repositorio remoto si no existe y
        sube el primer commit.

        Returns:
            str: Resumen de la operación.
        """
        if not token or not owner or not repo:
            raise GitHubError(
                "Configura primero el token, el dueño y el repositorio."
            )

        steps = []
        self.create_gitignore(project_path)
        self.ensure_repo(project_path)

        # Determinar la rama por defecto.
        branch = self.current_branch(project_path) or "main"

        # Crear el repositorio remoto si no existe.
        if not self.repo_exists(token, owner, repo):
            self.create_repo(
                token, repo,
                private=private,
                description=f"Proyecto {repo}",
            )
            steps.append(
                f"Creado el repositorio '{repo}' en GitHub "
                f"({'privado' if private else 'público'})."
            )
        else:
            steps.append(f"El repositorio '{owner}/{repo}' ya existía; se usará.")

        # Remoto y primer commit.
        self.set_remote(project_path, owner, repo)
        commit_out = self.commit(project_path, message)
        steps.append(f"Commit local: {commit_out or 'sin cambios para commitear'}")

        push_out = self.push(project_path, token, owner, repo, branch)
        steps.append(f"Push: {push_out}")

        url = f"{GITHUB_HTTPS}/{owner}/{repo}"
        steps.append(f"URL del repositorio: {url}")
        return "\n".join(steps)

    def push_changes(self, project_path, token, owner, repo, message):
        """Confirma los cambios locales y los sube al remoto."""
        if not self.is_repo(project_path):
            raise GitHubError(
                "El proyecto aún no es un repositorio git. Usa "
                "'Publicar proyecto en GitHub' para iniciarlo."
            )
        branch = self.current_branch(project_path)
        if not branch:
            raise GitHubError(
                "No hay ninguna rama/commit local todavía. Publica el "
                "proyecto primero para crear el primer commit."
            )
        commit_out = self.commit(project_path, message)
        push_out = self.push(project_path, token, owner, repo, branch)
        return f"Commit local: {commit_out}\nPush: {push_out}"

    def sync_pull(self, project_path, token, owner, repo):
        """Descarga los cambios remotos al proyecto local (pull)."""
        if not self.is_repo(project_path):
            raise GitHubError(
                "El proyecto aún no es un repositorio git. Usa "
                "'Publicar proyecto en GitHub' para iniciarlo."
            )
        branch = self.current_branch(project_path)
        if not branch:
            raise GitHubError(
                "No hay una rama local todavía. Publica el proyecto primero."
            )
        return self.pull(project_path, token, owner, repo, branch)
# ----------------------------------------------------------------------
# Diálogo de configuración de GitHub (interfaz gráfica)
# ----------------------------------------------------------------------

try:
    import tkinter as tk
    from tkinter import ttk, messagebox

    def _has_tk():
        return True
except Exception:  # Si no hay entorno gráfico (pruebas/headless).
    _has_tk = lambda: False


class GitHubCredentialsDialog:
    """Diálogo para configurar el token, dueño y repositorio de GitHub.

    Permite guardar las credenciales de forma persistente y validar el
    token contra la GitHub REST API antes de guardar.
    """

    def __init__(self, parent, sync, on_saved=None):
        """Inicializa el diálogo modal.

        Args:
            parent: Ventana padre (MainWindow).
            sync: Instancia de GitHubSync con la configuración a editar.
            on_saved: Callback invocado tras guardar correctamente.
        """
        self.sync = sync
        self.on_saved = on_saved
        cfg = sync.load_config()

        self.win = tk.Toplevel(parent)
        self.win.title("Configuración de GitHub")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        body = ttk.Frame(self.win, padding=14)
        body.pack(fill="both", expand=True)

        ttk.Label(
            body,
            text=(
                "Pega tu Personal Access Token de GitHub para poder\n"
                "publicar y sincronizar tus proyectos."
            ),
            justify="left",
        ).pack(anchor="w")

        # Token
        ttk.Label(body, text="Token (Personal Access Token):").pack(
            anchor="w", pady=(10, 2)
        )
        self.token_var = tk.StringVar(value=cfg.get("token", ""))
        self.token_entry = ttk.Entry(body, textvariable=self.token_var, width=48,
                                     show="*")
        self.token_entry.pack(fill="x")

        # Dueño
        ttk.Label(body, text="Dueño (usuario u organización):").pack(
            anchor="w", pady=(10, 2)
        )
        self.owner_var = tk.StringVar(value=cfg.get("owner", ""))
        ttk.Entry(body, textvariable=self.owner_var, width=48).pack(fill="x")

        # Repositorio
        ttk.Label(body, text="Nombre del repositorio:").pack(
            anchor="w", pady=(10, 2)
        )
        self.repo_var = tk.StringVar(value=cfg.get("repo", ""))
        ttk.Entry(body, textvariable=self.repo_var, width=48).pack(fill="x")

        # Privacidad
        self.private_var = tk.BooleanVar(value=bool(cfg.get("private", False)))
        ttk.Checkbutton(
            body, text="Repositorio privado", variable=self.private_var
        ).pack(anchor="w", pady=(10, 2))

        # Botones
        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(16, 0))
        ttk.Button(buttons, text="Guardar y validar", command=self._save).pack(
            side="left"
        )
        ttk.Button(buttons, text="Cancelar", command=self.win.destroy).pack(
            side="right"
        )

        self.win.bind("<Return>", lambda e: self._save())
        self.win.update_idletasks()
        self._center(parent)

    def _center(self, parent):
        """Centra el diálogo sobre la ventana padre."""
        try:
            parent.update_idletasks()
            pw, ph = parent.winfo_width(), parent.winfo_height()
            px, py = parent.winfo_rootx(), parent.winfo_rooty()
            w, h = self.win.winfo_reqwidth(), self.win.winfo_reqheight()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
            self.win.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass

    def _save(self):
        """Valida el token y guarda la configuración."""
        token = self.token_var.get().strip()
        owner = self.owner_var.get().strip()
        repo = self.repo_var.get().strip()

        if not token:
            messagebox.showwarning(
                "Falta el token",
                "Debes indicar tu Personal Access Token de GitHub.",
                parent=self.win,
            )
            return
        if not owner:
            messagebox.showwarning(
                "Falta el dueño",
                "Indica el usuario/organización dueño del repositorio.",
                parent=self.win,
            )
            return
        if not repo:
            messagebox.showwarning(
                "Falta el repositorio",
                "Indica el nombre del repositorio.",
                parent=self.win,
            )
            return

        # Validar el token contra la API (rápido y no bloquea demasiado).
        self.win.config(cursor="watch")
        self.win.update_idletasks()
        try:
            login = self.sync.get_authenticated_user(token)
        except Exception as e:
            self.win.config(cursor="")
            messagebox.showerror(
                "Token inválido",
                f"No se pudo validar el token:\n{e}",
                parent=self.win,
            )
            return

        self.win.config(cursor="")
        # Si el dueño coincide con el login, rellenar automáticamente.
        if not owner or owner == login:
            owner = login
            self.owner_var.set(login)

        cfg = self.sync.set_credentials(
            token, owner=owner, repo=repo, private=self.private_var.get()
        )
        if self.on_saved:
            self.on_saved(cfg)
        self.win.destroy()