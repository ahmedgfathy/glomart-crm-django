# Temporary settings for migrating to new MariaDB database
import sys
import os
sys.path.append('/Users/ahmedgomaa/Downloads/crm')
from real_estate_crm.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_db_glomart_rs',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'zerocall',
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}