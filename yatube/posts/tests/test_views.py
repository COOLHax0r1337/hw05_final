from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.cache import cache

from ..models import Post, Group, Follow

User = get_user_model()

RANGE_POSTS = 12
PAGINATE_PAGE_SECOND = 3
POST_LIMIT_SECOND = 10


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Группа фэнов графа',
            slug='slug',
            description='Инфа о группе'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст 11',
            group=cls.group,
        )
        cls.GROUP_LIST_URL = reverse(
            'posts:group_posts', kwargs={'slug': f'{cls.group.slug}'}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.user.username}'}
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.id}
        )
        cls.INDEX_URL = reverse('posts:index')
        cls.CREATE_POST_URL = reverse('posts:post_create')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewTests.user)
        posts: list = []
        for num in range(RANGE_POSTS):
            posts.append(
                Post(
                    text=f'Тестовый текст {num}',
                    group=self.group,
                    author=self.user,
                )
            )
        Post.objects.bulk_create(posts)

    def post_exist(self, page_context):
        if 'page_obj' in page_context:
            post = page_context['page_obj'][0]
        else:
            post = page_context['post']
        task_author = post.author
        task_text = post.text
        task_group = post.group
        self.assertEqual(
            task_author,
            PostViewTests.post.author
        )
        self.assertEqual(
            task_text,
            PostViewTests.post.text
        )
        self.assertEqual(
            task_group,
            PostViewTests.post.group
        )

    def test_first_and_second_pages_contains_ten_records(self):
        pages = (
            self.INDEX_URL,
            self.PROFILE_URL,
            self.GROUP_LIST_URL,
        )
        for page in pages:
            page_numbers = {
                page: settings.POST_LIMIT,
                ((page) + '?page=2'): PAGINATE_PAGE_SECOND
            }
            for page_number, count_page in page_numbers.items():
                with self.subTest(page_number=page_number):
                    response = self.client.get(page_number)
                    self.assertEqual(
                        len(response.context['page_obj']), count_page
                    )

    def test_index_show_correct_context(self):
        response_index = self.authorized_client.get(self.INDEX_URL)
        page_index_context = response_index.context
        self.post_exist(page_index_context)

    def test_post_detail_show_correct_context(self):
        response_post_detail = self.authorized_client.get(self.POST_DETAIL_URL)
        page_post_detail_context = response_post_detail.context
        self.post_exist(page_post_detail_context)

    def test_group_page_show_correct_context(self):
        response_group = self.authorized_client.get(self.GROUP_LIST_URL)
        page_group_context = response_group.context
        task_group = response_group.context['group']
        self.post_exist(page_group_context)
        self.assertEqual(task_group, PostViewTests.group)

    def test_views_post_added_correctly(self):
        post = Post.objects.create(
            text='Тест текст',
            author=self.user,
            group=self.group,
        )
        mapping = (
            self.authorized_client.get(self.INDEX_URL),
            self.authorized_client.get(self.GROUP_LIST_URL),
            self.authorized_client.get(self.PROFILE_URL),
        )
        for response in mapping:
            object = response.context['page_obj']
            self.assertIn(post, object)

    def test_profile_show_correct_context(self):
        response_profile = self.authorized_client.get(self.PROFILE_URL)
        page_profile_context = response_profile.context
        task_profile = response_profile.context['author']
        self.post_exist(page_profile_context)
        self.assertEqual(task_profile, PostViewTests.user)

    def test_views_create_post_and_post_edit_pages_show_correct_context(self):
        post_context = (
            self.CREATE_POST_URL,
            self.POST_EDIT_URL
        )
        for context in post_context:
            response = self.authorized_client.get(context)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField}
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_paginator_correct_context(self):
        paginator_objects = []
        for post_num in range(1, 18):
            new_post = Post(
                author=PostViewTests.user,
                text='Тестовый пост ' + str(post_num),
                group=PostViewTests.group
            )
            paginator_objects.append(new_post)
        Post.objects.bulk_create(paginator_objects)
        paginator_data = (
            self.INDEX_URL,
            self.GROUP_LIST_URL,
            self.PROFILE_URL,
        )
        for paginator_page in paginator_data:
            page_numbers = {
                paginator_page: settings.POST_LIMIT,
                ((paginator_page) + '?page=2'): POST_LIMIT_SECOND,
            }
            for page_number, count_page in page_numbers.items():
                with self.subTest(page_number=page_number):
                    response = self.client.get(page_number)
                    self.assertEqual(
                        len(response.context['page_obj']), count_page
                    )

    def test_cached_index_page(self):
        response = self.authorized_client.get(self.INDEX_URL)
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.user,
        )
        response_old = self.authorized_client.get(self.INDEX_URL)
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(self.INDEX_URL)
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_wrong_url_returns_custom_404(self):
        response = self.client.get('/wrong_url/')
        self.assertEqual(response.status_code, 404)

    def test_following_authors(self):
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='Mayakovsky')
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': new_author.username}
            )
        )
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author, new_author)
        self.assertEqual(follow.user, PostViewTests.user)

    def test_unfollowing_authors(self):
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='Mayakovsky')
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': new_author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': new_author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_following_posts_are_in_feed(self):
        new_user = User.objects.create(username='Mayakovsky')
        authorized_client = Client()
        authorized_client.force_login(new_user)
        authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user}
            )
        )
        response_follow = authorized_client.get(
            reverse('posts:follow_index')
        )
        context_follow = response_follow.context
        self.post_exist(context_follow)

    def test_unfollowed_posts_are_in_feed(self):
        new_user = User.objects.create(username='Mayakovsky')
        authorized_client = Client()
        authorized_client.force_login(new_user)
        response_unfollow = authorized_client.get(
            reverse('posts:follow_index')
        )
        context_unfollow = response_unfollow.context
        self.assertEqual(len(context_unfollow['page_obj']), 0)
