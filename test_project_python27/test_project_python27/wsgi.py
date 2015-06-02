"""
WSGI config for test_project_python27 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_project_python27.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
