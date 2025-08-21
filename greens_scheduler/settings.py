import os
from pathlib import Path
from celery.schedules import crontab

# -----------------------------
# .env (variáveis de ambiente)
# -----------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# -----------------------------
# Diretórios base
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------
# Configurações básicas
# -----------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]

# Nome do pacote do projeto (override via DJANGO_PROJECT se necessário)
PROJECT_MODULE = os.getenv("DJANGO_PROJECT", "greens_scheduler")

# -----------------------------
# Aplicativos
# (mantenha/adicione suas apps locais abaixo)
# -----------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "simple_history",
    "crm",
    # --- suas apps locais aqui ---
    # "agenda",
    # "accounts",
]

# -----------------------------
# Middleware
# -----------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    
]

# -----------------------------
# URLs / WSGI / ASGI
# -----------------------------
ROOT_URLCONF = f"{PROJECT_MODULE}.urls"
WSGI_APPLICATION = f"{PROJECT_MODULE}.wsgi.application"
# Se você tiver ASGI, descomente:
# ASGI_APPLICATION = f"{PROJECT_MODULE}.asgi.application"

# -----------------------------
# Templates
# -----------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

# -----------------------------
# Banco de dados (Postgres)
# -----------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "greens_prm"),
        "USER": os.getenv("POSTGRES_USER", "greens"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "greens"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": int(os.getenv("POSTGRES_PORT", "5432")),
        "CONN_MAX_AGE": int(os.getenv("POSTGRES_CONN_MAX_AGE", "60")),
    }
}

# --- Fallback para SQLite (usado no CI e, se quiser, no dev local) ---
if os.getenv("USE_SQLITE", "0") == "1":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# -----------------------------
# Internacionalização / Fuso
# -----------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# -----------------------------
# Arquivos estáticos
# -----------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------
# Autenticação
# -----------------------------
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

# -----------------------------
# Cache (opcional, simples)
# -----------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# -----------------------------
# Celery / Redis
# -----------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "0") == "1"

# Agenda / Google Calendar (flag já existente)
GOOGLE_CALENDAR_SYNC = os.getenv("GOOGLE_CALENDAR_SYNC", "0") == "1"

# -----------------------------
# Logs (stdout)
# -----------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}

# -----------------------------
# Sentry (erros em produção)
# -----------------------------
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            send_default_pii=False,
            environment=os.getenv("ENVIRONMENT", "dev"),
        )
    except Exception:
        # Sentry é opcional; se faltar pacote, apenas ignore
        pass

CELERY_BEAT_SCHEDULE = {
    "heartbeat-cada-minuto": {
        "task": "algum_app.tasks.heartbeat",
        "schedule": crontab(),  # a cada minuto
    }
}
