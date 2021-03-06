import json
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connections
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from healthcheck.contrib.django.status_endpoint import views


if not settings.configured:
    settings.configure()


class StatusEndpointViewsTestCase(TestCase):
    urls = 'healthcheck.contrib.django.status_endpoint.urls'

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(
        STATUS_CHECK_DBS=True,
        STATUS_CHECK_FILES=('/etc/quiesce',)
    )
    def test_default_checks(self):
        request = self.factory.get(reverse(views.status))
        response = views.status(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(
        STATUS_CHECK_DBS=True,
        STATUS_CHECK_FILES=()
    )
    def test_dont_check_files(self):
        request = self.factory.get(reverse(views.status))
        response = views.status(request)
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
    def test_no_checks_raises_200(self):
        request = self.factory.get(reverse(views.status))
        response = views.status(request)
        response = {
            'content': json.loads(response.content),
            'status': response.status_code,
        }

        expected_response = {
            'content': 'There were no checks.',
            'status': 200,
        }

        self.assertEqual(response, expected_response)
