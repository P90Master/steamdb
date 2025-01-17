from pathlib import Path

import os

from utils.enums import CountryCodes


#from dotenv import load_dotenv

# FIXME In future loading from docker container environment
#dotenv_path = os.path.abspath(os.path.join(os.getcwd(), '..', '.env'))

#if os.path.exists(dotenv_path):
#    load_dotenv(dotenv_path)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = os.getenv('DEBUG', False)

ALLOWED_HOSTS = [
    "*"
]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'games.apps.GamesConfig',
    'api.apps.ApiConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # TODO: Debug configuration & switch
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# Backend database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('BACKEND_DB_NAME', 'backend'),
        'USER': os.getenv('BACKEND_DB_USER', 'postgres'),
        'PASSWORD': os.getenv('BACKEND_DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('BACKEND_DB_HOST', 'localhost'),
        'PORT': int(os.getenv('BACKEND_DB_PORT', '5432')),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# API
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10,
}
API_VERSION = os.getenv('BACKEND_API_VERSION', 'v1')

# Orchestrator
ORCHESTRATOR_PROTOCOL = os.getenv('ORCHESTRATOR_PROTOCOL', "http")
ORCHESTRATOR_HOST = os.getenv('ORCHESTRATOR_HOST', "127.0.0.1")
ORCHESTRATOR_PORT = os.getenv('ORCHESTRATOR_PORT', 8888)
# TODO: advanced URL builder
ORCHESTRATOR_URL: str = f'{ORCHESTRATOR_PROTOCOL}://{ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}'
ORCHESTRATOR_API_VERSION = os.getenv('ORCHESTRATOR_API_VERSION', 'v1')

# Internationalization
LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{os.getenv("CACHE_HOST", "localhost")}:{os.getenv("CACHE_PORT", 6379)}/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 60 * 20))

# Games database
MONGO_HOST = os.getenv('MONGO_HOST', "127.0.0.1")
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_ALIAS = os.getenv('MONGO_ALIAS')
MONGO_DB = os.getenv('MONGO_DB', 'games')

# Business logic
DEFAULT_COUNTRY_CODE = os.getenv('DEFAULT_COUNTRY_CODE', CountryCodes.united_states.value)
