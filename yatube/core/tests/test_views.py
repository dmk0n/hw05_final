from http import HTTPStatus

from django.test import TestCase, Client


class ViewTestClass(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client()
        super().setUpClass()

    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
