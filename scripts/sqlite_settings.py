# Settings to use original SQLite database for data export
import os
from real_estate_crm.settings import *

# Override database to use original SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}