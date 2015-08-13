"""
WSGI config for deploy project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os,sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deploy.settings")
sys.path.append('/usr/local/apache/htdocs/deploy/')

application = get_wsgi_application()
