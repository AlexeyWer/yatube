import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_data = {
            'username': 'AlexeyTestov',
            'group_slug': 'test-slug',
            'group_title': 'Тестовая группа',
            'group_description': 'Тестовое описание',
            'post_text': 'Текст публикации',
            'new_post_text': 'Текст новой публикации',
            'uploaded_content': (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                                 b'\x01\x00\x80\x00\x00\x00\x00\x00'
                                 b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                                 b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                                 b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                                 b'\x0A\x00\x3B'),
            'uploaded_name_1': 'small1.gif',
            'uploaded_name_2': 'small2.gif',
            'uploaded_type': 'image/gif'
        }
        cls.user = User.objects.create_user(username=cls.test_data['username'])
        cls.group = Group.objects.create(
            title=cls.test_data['group_title'],
            slug=cls.test_data['group_slug'],
            description=cls.test_data['group_description'],
        )
        cls.post = Post.objects.create(
            text=cls.test_data['post_text'],
            group=cls.group,
            author=cls.user,
        )
        cls.pages_name_to_reverse = {
            'post_create': reverse('posts:post_create'),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}
            ),
            'post_edit': reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.pk}
            ),
            'post_detail': reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.pk}
            ),
            'login': reverse('users:login'),
            'add_comment': reverse(
                'posts:add_comment',
                kwargs={'post_id': cls.post.pk}
            ),

        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTest.user)

    def test_post_creation_form(self):
        """При отправке валидной формы со страницы создания
        поста создаётся новая запись в базе данных."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name=PostCreateFormTest.test_data['uploaded_name_1'],
            content=PostCreateFormTest.test_data['uploaded_content'],
            content_type=PostCreateFormTest.test_data['uploaded_type'],
        )
        form_data = {
            'text': PostCreateFormTest.test_data['new_post_text'],
            'group': PostCreateFormTest.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            PostCreateFormTest.pages_name_to_reverse['post_create'],
            data=form_data,
            follow=True,
            format='multipart/form-data',
        )
        self.assertRedirects(
            response,
            PostCreateFormTest.pages_name_to_reverse['profile']
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=PostCreateFormTest.test_data['new_post_text'],
                group=PostCreateFormTest.group,
                author=PostCreateFormTest.user,
                image=(f'posts/'
                       f'{PostCreateFormTest.test_data["uploaded_name_1"]}')
            ).exists()
        )

    def test_post_edit_form(self):
        """При отправке валидной формы со страницы редактирования
        поста происходит изменение поста в базе данных."""
        uploaded = SimpleUploadedFile(
            name=PostCreateFormTest.test_data['uploaded_name_2'],
            content=PostCreateFormTest.test_data['uploaded_content'],
            content_type=PostCreateFormTest.test_data['uploaded_type'],
        )
        post_edit_data = {
            'text': 'Обновленная запись',
            'group': '',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            PostCreateFormTest.pages_name_to_reverse['post_edit'],
            data=post_edit_data,
            follow=True,
            format='multipart/form-data',
        )
        self.assertRedirects(
            response,
            PostCreateFormTest.pages_name_to_reverse['post_detail']
        )
        self.assertTrue(
            Post.objects.filter(
                pk=PostCreateFormTest.post.pk,
                text=post_edit_data['text'],
                group=None,
                image=(f'posts/'
                       f'{PostCreateFormTest.test_data["uploaded_name_2"]}'),
            ).exists()
        )

    def test_anonymous_user_cant_create_post(self):
        """Не авторизованный пользователь не может создать новый пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': PostCreateFormTest.test_data['new_post_text'],
            'group': PostCreateFormTest.group.pk,
        }
        response = self.guest_client.post(
            PostCreateFormTest.pages_name_to_reverse['post_create'],
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            PostCreateFormTest.pages_name_to_reverse['login']
            + '?next='
            + PostCreateFormTest.pages_name_to_reverse["post_create"]
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_anonymous_user_cant_edit_post(self):
        """Анонимный пользователь не может отредактировать пост."""
        post_edit_data = {
            'text': 'Обновленная запись',
            'group': '',
        }

        response = self.guest_client.post(
            PostCreateFormTest.pages_name_to_reverse['post_edit'],
            data=post_edit_data,
            follow=True
        )
        self.assertRedirects(
            response,
            PostCreateFormTest.pages_name_to_reverse['login']
            + '?next='
            + PostCreateFormTest.pages_name_to_reverse["post_edit"]
        )
        self.assertFalse(
            Post.objects.filter(
                pk=PostCreateFormTest.post.pk,
                text=post_edit_data['text'],
                group=None
            ).exists()
        )

    def test_only_auth_user_can_comment_post(self):
        """Комментировать пост может только авторизованный пользователь."""
        comment = {
            'text': 'Текст комментария',
        }
        comment_count = PostCreateFormTest.post.comments.count()
        response = self.authorized_client.post(
            PostCreateFormTest.pages_name_to_reverse['add_comment'],
            data=comment,
            follow=True
        )
        last_comment = response.context['comments'].last()
        self.assertEqual(
            response.context['comments'].count(),
            comment_count + 1
        )
        self.assertEqual(last_comment.text, comment['text'])

    def test_guest_user_can_not_comment_post(self):
        """Неавторизованный пользователь не может комментировать пост."""
        comment = {
            'text': 'Текст комментария',
        }
        response = self.guest_client.post(
            PostCreateFormTest.pages_name_to_reverse['add_comment'],
            data=comment,
            follow=True
        )
        self.assertRedirects(
            response,
            PostCreateFormTest.pages_name_to_reverse['login']
            + '?next='
            + PostCreateFormTest.pages_name_to_reverse["add_comment"]
        )
