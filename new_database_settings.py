
# Add this to your settings.py DATABASES configuration:

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'USER': 'django_user',  # Changed from 'root'
        'PASSWORD': 'Django2024!Secure',  # New secure password
        'HOST': 'localhost',
        'PORT': '',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
