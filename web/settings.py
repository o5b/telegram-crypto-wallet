import os
from dotenv import load_dotenv

load_dotenv()
import os

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-_@lce#i^+a^+r$a#fl)+k*qu&(jx!n0f3nph4xez2j)@y=_#-0')
DEBUG = bool(int(os.getenv('DJANGO_DEBUG', 0)))
# DEBUG = True    # for local dev
ALLOWED_HOSTS = [os.getenv('DJANGO_ALLOWED_HOSTS', '*')]
ADMINS = (('Admin', 'admin.com'),)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'applications.account',
    'applications.wallet',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates/')],
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

WSGI_APPLICATION = 'web.wsgi.application'
ASGI_APPLICATION = 'web.asgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['POSTGRES_DB'],
            'USER': os.environ['POSTGRES_USER'],
            'PASSWORD': os.environ['POSTGRES_PASSWORD'],
            'HOST': os.environ['POSTGRES_HOST'],
            'PORT': os.environ['POSTGRES_PORT'],
        }
    }


AUTH_USER_MODEL = 'account.User'


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

# # STATICFILES_DIRS = (os.path.join(BASE_DIR, 'frontend'),)    # здесь collectstatic также будет искать статические файлы
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')              # сюда collectstatic поместит найденные стат. файлы
# STATIC_URL = '/static/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# MEDIA_URL = '/media/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.getenv('DJANGO_MEDIA_ROOT', '')

# URL that handles the media served from MEDIA_ROOT.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = os.getenv('DJANGO_MEDIA_URL', 'media/')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
if DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
else:
    STATIC_ROOT = os.getenv('DJANGO_STATIC_ROOT')
    STATICFILES_DIRS = [BASE_DIR / 'static']


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


if not DEBUG:
    from typing import List, Optional

    TRUE = ('1', 'true', 'True', 'TRUE', 'on', 'yes')

    def is_true(val: Optional[str]) -> bool:
        return val in TRUE

    def split_with_comma(val: str) -> List[str]:
        return list(filter(None, map(str.strip, val.split(','))))

    # Sessions
    SESSION_COOKIE_SECURE = is_true(os.getenv('DJANGO_SESSION_COOKIE_SECURE'))

    # Settings for CSRF cookie.
    CSRF_COOKIE_SECURE = is_true(os.getenv('DJANGO_CSRF_COOKIE_SECURE'))
    CSRF_TRUSTED_ORIGINS = split_with_comma(os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', ''))

    # Security Middleware (manage.py check --deploy)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 * 2  # 2 weeks, default - 0
    SECURE_SSL_REDIRECT = is_true(os.getenv('DJANGO_SECURE_SSL_REDIRECT'))
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


if DEBUG:
    try:
        from .local_settings import *
    except ImportError:
        pass
