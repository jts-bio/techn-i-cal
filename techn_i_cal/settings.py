from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-rc@04_mry_3-$@2sq$b9%-9jp6q2eyxf4bsw9&&esj++aw&r)p"


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "flowrate.herokuapp.com",
    "flowratetime.herokuapp.com",
    "flowratex.herokuapp.com",
    "jsteinbecker.pythonanywhere.com",
    "localhost",
    "127.0.0.1",
]


# Application definition

INSTALLED_APPS = [
    "schedule.apps.ScheduleConfig",
    "prd.apps.PrdConfig",
    "empl.apps.EmplConfig",
    "flow.apps.FlowConfig",
    "wday.apps.WdayConfig",
    "pds.apps.PdsConfig",
    "sch.apps.SchConfig",

    "sch.templatetags.tags",
    "wday.templatetags.wtags",
    
    "debug_toolbar",
    "slippers",
    "computedfields",
    "multiselectfield",
    "compressor",
    "taggit",
    "rest_framework",
    "django_filters",
    "url_filter",
    "django_tables2",
    "grappelli",
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    # "kolo.middleware.KoloMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_require_login.middleware.LoginRequiredMiddleware",
]

LOGIN_URL = "login-view"
LOGOUT_REDIRECT_URL = "sch:index"

REQUIRE_LOGIN_PUBLIC_NAMED_URLS = (LOGIN_URL, LOGOUT_REDIRECT_URL)

ROOT_URLCONF = "techn_i_cal.urls"

TEST_RUNNER = "django.test.runner.DiscoverRunner"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / "templates/static" ],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                # PyPugJS part: ~~~~~~~~~~~
                ('pypugjs.ext.django.Loader', (
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ))
            ],
            'builtins': ["slippers.templatetags.slippers",
                         'pypugjs.ext.django.templatetags'],  # Remove this line for Django 1.8
        },
    },
]

WSGI_APPLICATION = "techn_i_cal.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
# DATABASES = {
#     'default': {
#         'ENGINE':   'django.db.backends.postgresql',
#         'NAME':     'jsteinbecker/flowratex',
#         'USER':     'jsteinbecker',
#         'PASSWORD': 'v2_42mJQ_yCnLWhz8VHCH9BHragb8tCM',
#         'HOST':     'db.bit.io',
#         'PORT':     '5432',
#     }
# }
# DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

PYDEVD_UNBLOCK_THREADS_TIMEOUT = 240
# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "MST"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / 'svelte/static',
    ]
STATIC_ROOT = STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"


# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}