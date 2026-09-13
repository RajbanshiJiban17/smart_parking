"""
WSGI config for smart_parking project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_parking.settings')

application = get_wsgi_application()

# Auto-initialize database tables and seed data if missing on cloud platforms (e.g. Render)
try:
    from django.core.management import call_command
    from django.db import connection
    table_names = connection.introspection.table_names()
    if 'auth_user' not in table_names:
        print("Auto-running migrations on startup...")
        call_command('migrate', interactive=False)
        try:
            call_command('seed_data')
        except Exception as seed_err:
            print(f"Seed data notice: {seed_err}")
except Exception as err:
    print(f"Auto-migration notice: {err}")

