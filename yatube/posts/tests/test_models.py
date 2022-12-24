from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()

POST_LENGTH = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_model_post_group_have_correct_obj_names(self):
        field_str = (
            (str(self.post), self.post.text[:POST_LENGTH]),
            (str(self.group), self.group.title),
        )
        for value, expected_value in field_str:
            with self.subTest(value=value):
                self.assertEqual(value, expected_value)

    def test_verbose_name(self):
        post = PostModelTest.post
        verbose_names = {
            'text': 'Текст',
            'pub_date': 'pub date',
            'author': 'author',
            'group': 'Группа',
        }
        for field, expected_value in verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Текст вашего поста',
            'group': 'Укажите название группы',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )
