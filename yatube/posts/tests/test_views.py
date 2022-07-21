import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post
from ..forms import PostForm


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.test_data = {
            'group_title': 'Тестовая группа № 1',
            'group_slug': 'test-slug-1',
            'group_description': 'Тестовое описание',
            'post_text': 'Тестовый пост № 1',
            'uploaded_content': (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                                 b'\x01\x00\x80\x00\x00\x00\x00\x00'
                                 b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                                 b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                                 b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                                 b'\x0A\x00\x3B'),
            'uploaded_name': 'small.gif',
            'uploaded_type': 'image/gif'
        }
        cls.uploaded = SimpleUploadedFile(
            name=cls.test_data['uploaded_name'],
            content=cls.test_data['uploaded_content'],
            content_type=cls.test_data['uploaded_type'],
        )
        cls.user = User.objects.create_user(username='AlexeyTestov')
        cls.second_user = User.objects.create_user(username='AlexeyTestov2')
        cls.third_user = User.objects.create_user(username='AlexeyTestov3')
        cls.group = Group.objects.create(
            title=cls.test_data['group_title'],
            slug=cls.test_data['group_slug'],
            description=cls.test_data['group_description'],
        )
        cls.post = Post.objects.create(
            text=cls.test_data['post_text'],
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.templates_page_names = {
            'index': (
                reverse('posts:index'),
                'posts/index.html'
            ),
            'group_list': (
                reverse(
                    'posts:group_list',
                    kwargs={'slug': f'{cls.post.group.slug}'}
                ),
                'posts/group_list.html'
            ),
            'profile': (
                reverse(
                    'posts:profile',
                    kwargs={'username': cls.user.username}
                ),
                'posts/profile.html'
            ),
            'post_detail': (
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': cls.post.pk}
                ),
                'posts/post_detail.html'
            ),
            'post_edit': (
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': cls.post.pk}
                ),
                'posts/create_post.html'
            ),
            'post_create': (
                reverse('posts:post_create'),
                'posts/create_post.html'
            ),
        }
        cls.follow_urls = {
            'follow_index': reverse('posts:follow_index'),
            'follow': reverse(
                'posts:profile_follow',
                kwargs={'username': cls.user.username}
            ),
            'unfollow': reverse(
                'posts:profile_unfollow',
                kwargs={'username': cls.user.username}
            )
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTest.user)
        self.second_authorized_client = Client()
        self.second_authorized_client.force_login(PostPagesTest.second_user)
        self.third_authorized_client = Client()
        self.third_authorized_client.force_login(PostPagesTest.third_user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for (reverse_name,
             template) in PostPagesTest.templates_page_names.values():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            PostPagesTest.templates_page_names['index'][0]
        )
        first_post = response.context['page_obj'][0]
        first_post_data_expected = {
            (first_post.text): (PostPagesTest.post.text),
            (first_post.author.username): (PostPagesTest.user.username),
            (first_post.group.slug): (PostPagesTest.post.group.slug)
        }
        for object, expected in first_post_data_expected.items():
            with self.subTest(object=object):
                self.assertEqual(object, expected)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            PostPagesTest.templates_page_names['group_list'][0]
        )
        self.assertEqual(
            response.context['group'],
            PostPagesTest.group
        )
        first_post = response.context['page_obj'][0]
        first_post_group_slug = first_post.group.slug
        self.assertEqual(first_post_group_slug, PostPagesTest.group.slug)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            PostPagesTest.templates_page_names['profile'][0]
        )
        self.assertEqual(
            response.context['author'],
            PostPagesTest.user
        )
        first_post = response.context['page_obj'][0]
        first_post_author = first_post.author.username
        self.assertEqual(first_post_author, PostPagesTest.user.username)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            PostPagesTest.templates_page_names['post_detail'][0]
        )
        self.assertEqual(
            response.context['post'],
            PostPagesTest.post
        )

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            PostPagesTest.templates_page_names['post_create'][0]
        )
        self.assertIsInstance(response.context['form'], PostForm)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            PostPagesTest.templates_page_names['post_edit'][0]
        )
        self.assertEqual(
            response.context['form'].instance,
            PostPagesTest.post
        )

    def test_new_post_displayed_on_pages(self):
        """Новый пост отображается на главной странице,
        на странице выбранной группы, в профайле пользователя."""
        new_post = Post.objects.create(
            text='Совсем новый пост',
            author=PostPagesTest.user,
            group=PostPagesTest.group
        )
        urls_for_test = [
            PostPagesTest.templates_page_names['index'][0],
            PostPagesTest.templates_page_names['group_list'][0],
            PostPagesTest.templates_page_names['profile'][0]
        ]
        for url in urls_for_test:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                first_post = response.context['page_obj'][0]
                self.assertEqual(new_post, first_post)

    def test_auth_user_can_follow_and_unfollow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок."""
        response = self.second_authorized_client.get(
            PostPagesTest.templates_page_names['profile'][0]
        )
        self.assertFalse(response.context['following'])
        response = self.second_authorized_client.get(
            PostPagesTest.follow_urls['follow'],
            follow=True
        )
        self.assertTrue(response.context['following'])
        response = self.second_authorized_client.get(
            PostPagesTest.follow_urls['unfollow'],
            follow=True
        )
        self.assertFalse(response.context['following'])

    def test_view_following_posts(self):
        """Новая запись пользователя появляется в ленте тех, кто на
        него подписан и не появляется в ленте тех, кто не подписан."""
        self.second_authorized_client.get(
            PostPagesTest.follow_urls['follow'],
        )
        response = self.second_authorized_client.get(
            PostPagesTest.follow_urls['follow_index']
        )
        posts_count = len(response.context['page_obj'])
        new_post = Post.objects.create(
            text='New post text',
            group=PostPagesTest.group,
            author=PostPagesTest.user,
        )
        response = self.second_authorized_client.get(
            PostPagesTest.follow_urls['follow_index']
        )
        posts = response.context['page_obj']
        self.assertEqual(len(posts), posts_count + 1)
        self.assertEqual(posts[0], new_post)
        response = self.third_authorized_client.get(
            PostPagesTest.follow_urls['follow_index']
        )
        self.assertEqual(
            len(response.context['page_obj']),
            0
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.test_data = {
            'group_title': 'Тестовая группа № 1',
            'group_slug': 'test-slug-1',
            'group_description': 'Тестовое описание',
        }
        cls.user = User.objects.create_user(username='AlexeyTestov')
        cls.group = Group.objects.create(
            title=cls.test_data['group_title'],
            slug=cls.test_data['group_slug'],
            description=cls.test_data['group_description'],
        )
        cls.posts_count = settings.PUB_COUNT
        cls.templates_page_names = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}
            )
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)
        for i in range(PaginatorViewsTest.posts_count + 5):
            Post.objects.create(
                text=f'Тестовый пост № {i}',
                author=PaginatorViewsTest.user,
                group=PaginatorViewsTest.group
            )

    def test_first_pages_contains_pub_count_records(self):
        """Проверка на первой странице количество постов равно
        константе PUB_COUNT файла настроек."""
        for name, url in PaginatorViewsTest.templates_page_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    PaginatorViewsTest.posts_count
                )

    def test_second_pages_contains_five_records(self):
        """Проверка на второй странице количество постов равно пяти."""
        for name, url in PaginatorViewsTest.templates_page_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    5
                )


class PostCacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='AlexeyTestov')
        cls.post = Post.objects.create(
            text='Test post',
            author=cls.author
        )
        cls.urls = {
            'index': reverse('posts:index'),
        }

    def setUp(self):
        self.guest_client = Client()

    def test_index_cache(self):
        """Тестирование кэширования страницы index."""
        response = self.guest_client.get(PostCacheTest.urls['index'])
        Post.objects.filter(pk=PostCacheTest.post.id)
        second_response = self.guest_client.get(PostCacheTest.urls['index'])
        self.assertEqual(response.content, second_response.content)
