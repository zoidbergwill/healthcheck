import json
import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connections
from django.test import override_settings, TestCase
from django.test.client import Client

from healthcheck.contrib.django.status_endpoint import views


if not settings.configured:
    settings.configure(
        DATABASE_ENGINE='sqlite3',
        DATABASES={
            'default': {
                'NAME': ':memory:',
                'ENGINE': 'django.db.backends.sqlite3',
                'TEST_NAME': ':memory:',
            },
        },
        DATABASE_NAME=':memory:',
        TEST_DATABASE_NAME=':memory:',
        INSTALLED_APPS=['healthcheck.contrib.django.status_endpoint'],
        ROOT_URLCONF='',
        DEBUG=False,
        SITE_ID=1,
        TEMPLATE_DEBUG=True,
        PROJECT_ROOT=os.path.dirname(os.path.abspath(__file__)),
        ALLOWED_HOSTS=['*'],
    )


class StatusEndpointViewsTestCase(TestCase):
    urls = 'healthcheck.contrib.django.status_endpoint.urls'

    @override_settings(
        STATUS_CHECK_DBS=True,
        STATUS_CHECK_FILES=('/etc/quiesce',)
    )
    def test_default_checks(self):
        response = Client().get(reverse(views.status))
        self.assertEqual(response.status_code, 200)

    @override_settings(
        STATUS_CHECK_DBS=True,
        STATUS_CHECK_FILES=()
    )
    def test_dont_check_files(self):
        response = Client().get(reverse(views.status))
        response_json = json.loads(response.content)
        self.assertTrue(
            "quiesce file doesn't exist" not in response_json)
        self.assertTrue(
            'Django Databases Health Check' in response_json)
        db_names = response_json['Django Databases Health Check']['details']
        self.assertTrue(
            all(connection.alias in db_names
                for connection in connections.all()))
        self.assertEqual(response.status_code, 200)

    @override_settings(
        STATUS_CHECK_DBS=False,
        STATUS_CHECK_FILES=()
    )
    def test_no_checks_raises_500(self):
        # Pending related issue: https://github.com/yola/healthcheck/issues/10
        response = Client().get(reverse(views.status))
        response_json = json.loads(response.content)
        self.assertTrue(
            "quiesce file doesn't exist" not in response_json)
        self.assertTrue(
            'Django Databases Health Check' not in response_json)
        self.assertEqual(response.status_code, 500)