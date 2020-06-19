"""
Django settings for scg project.

Generated by 'django-admin startproject' using Django 3.0.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from django.contrib.messages import constants as message_constants
try:
    from . import credentials
except:
    pass

CURRENT_VERSION = '0.9.7'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'y=yxaf=l5p)+ogu1d3n2tn59$z(+%z)##uql@*pe5i^dhzmc7%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ['*']
PROTOCOL = 'http'
BASE_URL = 'localhost:8000'

# Application definition
INSTALLED_APPS = [
    #django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    

    #third
    'multiselectfield',
    'report_builder',
    'ckeditor',
    'ckeditor_uploader',
    'rest_framework',
    'django_extensions',
    #'simple_history',
    #'django_crontab',

    #own
    'scg_app',
    'api',
    'help',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'simple_history.middleware.HistoryRequestMiddleware',
]

SHELL_PLUS = 'notebook'

#for user messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
MESSAGE_TAGS = {message_constants.ERROR: 'danger'}  #fpr bootstrap style

ROOT_URLCONF = 'scg.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'scg.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'    #'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    #'/var/www/static/',
]
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR),'statics_pub')

#media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'media_uploads')
CKEDITOR_UPLOAD_PATH = "help/"

# tmp dir
TMP_DIR = os.path.join(os.path.dirname(BASE_DIR), 'tmp')

### reporting ###
#REPORT_BUILDER_ASYNC_REPORT = True
REPORT_BUILDER_INCLUDE = [
    'user',
    'scg_app.clase', 'scg_app.empleado', 'scg_app.actividad', 'scg_app.escala',
    'scg_app.grupoactividad', 'scg_app.marcaje', 'scg_app.motivoausencia',
    'scg_app.recurrencia', 'scg_app.saldo', 'scg_app.sede', 
    'scg_app.tipocontrato', 'scg_app.tipoliquidacion',
    'scg_app.bloquedepresencia', 'scg_app.certificado',
] # Allow only the model user to be accessed
#REPORT_BUILDER_FRONTEND = False

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/logout/?next=/'

#DRF
REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.IsAdminUser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

### password recovery ###
if 'credentials' in dir():
    EMAIL_USE_TLS = credentials.EMAIL_USE_TLS
    EMAIL_HOST = credentials.EMAIL_HOST
    EMAIL_PORT = credentials.EMAIL_PORT
    EMAIL_HOST_USER = credentials.EMAIL_HOST_USER
    EMAIL_HOST_PASSWORD = credentials.EMAIL_HOST_PASSWORD
    DEFAULT_FROM_EMAIL = credentials.DEFAULT_FROM_EMAIL
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

### SCG_APP specifics ###
SERVER_URL = "http://192.168.1.104:8091/webservice?"

MINS_TOLERACIA = 15
MINS_BTW_CLOCKS = 5 #minutes between clockings

DIA_SEMANA_CHOICES = (
    ("0", "Lunes"),
    ("1", "Martes"),
    ("2", "Miércoles"),
    ("3", "Jueves"),
    ("4", "Viernes"),
    ("5", "Sábado"),
    ("6", "Domingo"),
)

ESTADOS_CHOICES = (
    ("0", "Pendiente"),
    ("1", "Realizada"),
    ("2", "Reemplazado"),
    ("3", "Ausencia"),
    ("4", "Feriado"),
    #separate
    ("5", "Cancelada"), # keep last
)

PRESENCIA_CHOICES = (
    ("No Realizada", "No Realizada"),
    ("Realizada", "Realizada"),  # keep last
)

ACCIONES_CHOICES = (
    ("gestion_ausencia", "Gestión de Ausencia"),
    ("gestion_reemplazo", "Gestión de Reemplazo"),
    ("confirmacion", "Confirmación"),
    ("edicion", "Edición de Clase"),
    ("cancelacion", "Cancelación"),

    ("comentario", "Comentario"),   #keep last
)

#help editor
CKEDITOR_CONFIGS = {
    "default": {
        'skin': 'n1theme',
        "removePlugins": "flash",
        'toolbar_Basic': [['Source', '-', 'Bold', 'Italic']],
        'toolbar_YourCustomToolbarConfig': [
            {
                'name': 'styles',
                'items': [
                    'Styles', 'Format', 'Font', 'FontSize'
                ]
            },
            {'name': 'colors', 'items': ['TextColor', 'BGColor']},
            {'name': 'tools', 'items': ['Maximize', 'ShowBlocks', 'Preview']},
            '/',
            {'name': 'document', 'items': ['Source', '-']},
            {
                'name': 'clipboard',
                'items': ['Paste', 'PasteText', '-', 'Undo', 'Redo']
            },
            {'name': 'editing', 'items': ['Find', '-', 'SelectAll']},
            {
                'name': 'forms',
                'items': [
                    'Form', 'Checkbox', 'Radio', 'TextField', 'Textarea',
                    'Select', 'Button', 'ImageButton', 'HiddenField'
                ]
            },
            '/',
            {
                'name': 'basicstyles',
                'items': [
                    'Bold', 'Italic', 'Underline', 'Strike', 'Subscript',
                    'Superscript', '-', 'RemoveFormat'
                ]
            },
            {
                'name': 'paragraph',
                'items': [
                    'NumberedList', 'BulletedList', '-', 'Outdent', 'Indent',
                    '-', 'Blockquote', '-', 'JustifyLeft', 'JustifyCenter',
                    'JustifyRight', 'JustifyBlock', '-'
                ]
            },
            {'name': 'links', 'items': ['Link', 'Unlink', 'Anchor']},
            {
                'name': 'insert',
                'items': [
                    'Image', 'Flash', 'Table', 'HorizontalRule', 'Smiley',
                    'SpecialChar', 'PageBreak', 'Iframe', 'Youtube'
                ]
            },
        ],
        'toolbar': 'YourCustomToolbarConfig', # put selected toolbar config here
        'extraPlugins': 'youtube',

    }
}
