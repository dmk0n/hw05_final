from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_about_page_accessible_by_name(self):
        """URL, генерируемые при помощи имен about:author и about:author,
        доступны."""
        templates_pages_names = {
            reverse('about:author'): HTTPStatus.OK,
            reverse('about:tech'): HTTPStatus.OK,
        }
        for reverse_name, response_code in templates_pages_names.items():
            with self.subTest(response_code=response_code):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, response_code)

    def test_about_pages_use_correct_template(self):
        """URL-адреса about используют соответствующие шаблоны."""
        templates_pages_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
