# settings.py — tireinspect (produção com SQLite + .env interno)

from pathlib import Path
import os

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent          # /home/deploy/apps/tireinspect
PROJECT_DIR = Path(__file__).resolve().parent              # /home/deploy/apps/tireinspect/tireinspect

# Carregar .env (se python-dotenv estiver instalado)
try:
    from dotenv import load_dotenv  # pip install python-dotenv (opcional)
    load_dotenv(PROJECT_DIR / '.env')
    load_dotenv(BASE_DIR / '.env')
    load_dotenv(BASE_DIR.parent / '.env')
except Exception:
    # Se não houver python-dotenv, as variáveis podem vir do ambiente do sistema
    pass

# Helpers
def _get_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name, str(default))
    return str(val).strip().lower() in ('1', 'true', 'yes', 'on')

def _split_csv(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]

# Segurança e debug
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE-ME-IN-PROD")
DEBUG = _get_bool("DEBUG", False)

ALLOWED_HOSTS = _split_csv(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1"  # fallback seguro
)

CSRF_TRUSTED_ORIGINS = _split_csv("CSRF_TRUSTED_ORIGINS", "")

# Aplicativos instalados
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceiros
    "crispy_forms",
    "crispy_tailwind",
    # Apps do projeto
    "core",
    "reports",
    "inspection_reports",
    "service_orders",
]

# Middleware padrão
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tireinspect.urls"             # ajuste se seu pacote principal tiver outro nome

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],     # opcional: /home/deploy/apps/tireinspect/templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tireinspect.wsgi.application"  # ajuste se necessário

# Banco de dados — SQLite por padrão
# Para usar Postgres depois, defina DATABASE_URL no .env.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Opcional: habilitar DATABASE_URL se existir e dj-database-url estiver instalado
_database_url = os.getenv("DATABASE_URL")
if _database_url:
    try:
        import dj_database_url  # pip install dj-database-url (opcional)
        DATABASES["default"] = dj_database_url.parse(
            _database_url,
            conn_max_age=600,
            ssl_require=_get_bool("DB_SSL_REQUIRE", False),
        )
    except Exception:
        # Se o pacote não existir, mantemos o SQLite
        pass

# Internacionalização
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Arquivos estáticos e mídia
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

STATIC_ROOT = os.getenv("DJ_STATIC_ROOT", str(BASE_DIR / "staticfiles"))
MEDIA_ROOT = os.getenv("DJ_MEDIA_ROOT", str(BASE_DIR / "mediafiles"))

STATICFILES_DIRS = [BASE_DIR / "static"]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Em desenvolvimento local você pode adicionar:
# STATICFILES_DIRS = [BASE_DIR / "static"]

# Segurança / HTTPS (atrás do Nginx/Certbot)
SECURE_SSL_REDIRECT = _get_bool("SECURE_SSL_REDIRECT", False)
# Honra X-Forwarded-Proto enviado pelo Nginx
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Cookies seguros (ativar quando HTTPS estiver ativo)
SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT

# Padrões do Django 4+
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logs básicos (útil em produção)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO" if not DEBUG else "DEBUG",
    },
}

# Email (padrão: console). Troque para SMTP quando precisar.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Crispy Forms (Tailwind)
CRISPY_ALLOWED_TEMPLATE_PACKS = ("tailwind",)
CRISPY_TEMPLATE_PACK = "tailwind"

# Autenticação (URLs de redirecionamento)
LOGIN_URL = "core:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:login"
