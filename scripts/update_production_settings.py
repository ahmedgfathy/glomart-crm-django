# Production Database Settings Update
# Choose one of these options:


# ==========================================
# OPTION 1: Use dedicated Django user (RECOMMENDED)
# ==========================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'USER': 'django_prod',
        'PASSWORD': 'DjangoProd2024!Secure#',
        'HOST': 'localhost',
        'PORT': '',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}



# ==========================================
# OPTION 2: Fix root user configuration  
# ==========================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'USER': 'root',
        'PASSWORD': 'ZeroCall20!@HH##1655&&',  # Your actual production password
        'HOST': 'localhost',
        'PORT': '',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
