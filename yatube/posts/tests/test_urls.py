from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus

from ..models import Group, Post, User


class PostURLTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )
        cls.GROUP_LIST_URL = reverse(
            'posts:group_posts', kwargs={'slug': f'{cls.group.slug}'}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.user.username}'})
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.id}
        )
        cls.POST_CREATE_REDIRECT = '/auth/login/?next=/create/'
        cls.POST_EDIT_REDIRECT = (
            f'/auth/login/?next=/posts/{cls.post.id}/edit/')
        cls.INDEX_URL = reverse('posts:index')
        cls.CREATE_POST_URL = reverse('posts:post_create')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            self.INDEX_URL: 'posts/index.html',
            self.GROUP_LIST_URL: 'posts/group_list.html',
            self.PROFILE_URL: 'posts/profile.html',
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            self.CREATE_POST_URL: 'posts/create_post.html',
            self.POST_EDIT_URL: 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_exists_for_anonymus(self):
        url = (
            self.INDEX_URL,
            self.GROUP_LIST_URL,
            self.PROFILE_URL,
            self.POST_DETAIL_URL,
        )
        for adress in url:
            response = self.guest_client.get(adress)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_for_authorized(self):
        response = self.authorized_client.get(self.CREATE_POST_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_redirect_anonymous_on_login(self):
        pages = {
            self.CREATE_POST_URL: self.POST_CREATE_REDIRECT,
            self.POST_EDIT_URL: self.POST_EDIT_REDIRECT
        }
        for page, value in pages.items():
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertRedirects(response, value)

    def test_post_edit_for_author(self):
        response = self.authorized_client.get(self.POST_EDIT_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_guest(self):
        form_data = {
            'text': 'Текст в форме',
            'group': self.group.id
        }
        response = self.guest_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/')
