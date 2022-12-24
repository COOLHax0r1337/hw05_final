import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from http import HTTPStatus

from ..models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='test_group2',
            slug='test_slug2',
            description='Тестовое описание2'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{self.user.username}'})
        self.CREATE_POST_URL = reverse('posts:post_create')

    def test_auth_user_can_publish_post(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст2',
            'group': self.group.id,
            'author': self.user,
            'image': uploaded
        }
        response = self.authorized_client.post(
            self.CREATE_POST_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.last()
        mapping = {
            response.status_code: HTTPStatus.OK,
            Post.objects.count(): 1,
            post.text: form_data['text'],
            post.group.pk: form_data['group'],
            post.author: form_data['author'],
            post.image: 'posts/small.gif'
        }
        for object, value in mapping.items():
            with self.subTest(object=object):
                self.assertEqual(object, value)

    def test_forms_edit_post(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post = Post.objects.create(
            text='test',
            author=self.user,
            group=self.group,
        )
        form_data = {
            'text': 'Измененный тестовый текст',
            'group': self.group2.id,
            'image': uploaded
        }
        self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': post.id}
            ),
            data=form_data,
            follow=True
        )
        post = Post.objects.last()
        mapping = {
            post.text: form_data['text'],
            post.group.pk: form_data['group'],
            post.author: self.user
        }
        for form, value in mapping.items():
            with self.subTest(form=form):
                self.assertEqual(form, value)

    def test_unauth_user_cant_publish_post(self):
        form_data = {'text': 'Текст в форме'}
        response = self.guest_client.post(
            self.CREATE_POST_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_auth_user_can_create_comment_and_shows_on_page(self):
        post = Post.objects.create(
            text='test',
            author=self.user,
            group=self.group,
        )
        form_data = {
            'text': 'new comment'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': post.id}
            ),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.last()
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': post.id}
        ))
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
