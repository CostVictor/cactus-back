import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta

# Variáveis de ambiente.
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = True

ALLOWED_HOSTS = ("localhost", "192.168.3.102")

CORS_ALLOW_CREDENTIALS = True  # Permitir cookies em requisições CORS.
CORS_ALLOW_ALL_ORIGINS = False  # False para produção.

# Para restringir solicitações a dominios específicos.
CORS_ALLOWED_ORIGINS = ("http://192.168.3.102:3000",)

CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "PATCH",
    "POST",
    "PUT",
)


REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "limited_access": "5/minute",  # 5 requisições por minuto.
    },
}


SIMPLE_JWT = {
    "AUTH_COOKIE": "access_token",
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),  # 10 minutos para tokens de acesso.
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),  # Uma semana para o token de refresh.
    "AUTH_COOKIE_HTTP_ONLY": False,  # True para produção.
    "AUTH_COOKIE_SECURE": False,  # True para produção.
    "AUTH_COOKIE_SAMESITE": "Lax",  # Strict para produção.
}


# Application definition

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "sessionSC",
    "userSC",
    "snackSC",
    "lunchSC",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

ROOT_URLCONF = "cactus.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "cactus.wsgi.application"
ASGI_APPLICATION = "cactus.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 10,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "userSC.User"


LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
