import os
import dj_database_url
from pathlib import Path

# Base directory setup
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-custom-secret-key-change-this-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
# Isko False karna sabse zaroori hai
DEBUG = False

# Yahan apna domain aur Render ka default URL daalein
ALLOWED_HOSTS = ['cgsmart.in', 'www.cgsmart.in', '*'] 

# YEH NAYI LINE JODEIN (Aapke domain par secure login allow karne ke liye)
CSRF_TRUSTED_ORIGINS = ['https://cgsmart.in', 'https://www.cgsmart.in']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Aapka custom app
    'rest_framework',
    'products',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'store_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Niche wali line me humne Django ko sabhi folders me dhoondhne ko kaha hai
        'DIRS': [BASE_DIR / 'templates', BASE_DIR / 'products' / 'templates'], 
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

WSGI_APPLICATION = 'store_backend.wsgi.application'


# Agar Render par live hai, toh PostgreSQL use hoga, warna computer me SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(
        default=os.environ.get('DATABASE_URL')
    )

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization/Language Settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata' # Indian Time Zone ke mutabiq
USE_I18N = True
USE_TZ = True


# Static Files Setup (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
TATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==============================================================================
# 🎨 1. MEDIA & PRODUCT IMAGES SETTINGS (Added)
# ==============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# ==============================================================================
# 🔒 2. SECURITY UPGRADES MIDDLEWARE SETTINGS (Added)
# ==============================================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Jab aap website live domain aur HTTPS/SSL certificate laga lenge, 
# tab niche di gayi lines ko uncomment (aage se '#' hata kar) True kar sakte hain:
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
LOGIN_REDIRECT_URL = '/'

# 🔒 PRODUCTION SECURITY SETTINGS
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Render server proxy configuration for HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True