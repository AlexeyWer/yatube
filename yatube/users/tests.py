from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse


User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='AlexeyTestov')

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user)

    # Проверяем общедоступные страницы
    def test_signup_url_is_available_to_any_user(self):
        """Страница регистрации доступна любому пользователю."""
        response = self.guest_client.get('/auth/signup/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login_url_is_available_to_any_user(self):
        """Страница входа в профиль доступна любому пользователю."""
        response = self.guest_client.get('/auth/login/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_url_is_available_to_authorized_user(self):
        """Страница выхода из профиля доступна авторизованному пользователю."""
        response = self.authorized_client.get('/auth/logout/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/logout/': 'users/logged_out.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Создаем тестового пользователя
        cls.user = User.objects.create_user(username='AlexeyTestov')

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTest.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names_with_auth = {
            reverse(
                'users:logout'
            ): 'users/logged_out.html',
        }
        for reverse_name, template in templates_page_names_with_auth.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        templates_page_names_geust = {
            reverse(
                'users:signup'
            ): 'users/signup.html',
            reverse(
                'users:login'
            ): 'users/login.html',
        }
        for reverse_name, template in templates_page_names_geust.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_signup_form_context(self):
        """На странице signup в контекст передаётся форма для создания
        нового пользователя."""
        response = self.guest_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
            'password1': forms.fields.CharField,
            'password2': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)


class UsersCreateFormTest(TestCase):
    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()

    def test_signup_form(self):
        """Проверка - при отправке валидной формы со страницы
        создания пользователя создаётся новая запись в базе данных."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Alexey',
            'last_name': 'Testov',
            'username': 'AlexeyTestov',
            'email': 'alexeytestov@mail.ru',
            'password1': 'newpassdjango123',
            'password2': 'newpassdjango123',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:index')
        )
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(
            User.objects.filter(
                first_name='Alexey',
                last_name='Testov',
                username='AlexeyTestov',
                email='alexeytestov@mail.ru',
            )
        )
