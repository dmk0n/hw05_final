from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост Тестовый пост Тестовый пост',
        )
        cls.author_field = cls.post._meta.get_field('author')
        cls.text_field = cls.post._meta.get_field('text')

    def test_Post_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = self.post
        TEXT_LENGTH = 15
        expected_object_name = post.text[:TEXT_LENGTH]
        self.assertEqual(expected_object_name, str(post))

    def test_Post_verbose_name(self):
        """Тест параметра verbose_name у полей модели Post"""
        verbose_names = {
            getattr(self.author_field, 'verbose_name'): 'Автор',
            getattr(self.text_field, 'verbose_name'): 'Текст поста',
        }
        for real_verbose_name, expected_verbose_name in verbose_names.items():
            with self.subTest(real_verbose_name=real_verbose_name):
                self.assertEqual(real_verbose_name, expected_verbose_name)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = self.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост Тестовый пост Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Тестовый комментарий'
        )
        cls.author_field = cls.comment._meta.get_field('author')
        cls.post_field = cls.comment._meta.get_field('post')
        cls.text_field = cls.comment._meta.get_field('text')

    def test_Comment_verbose_name(self):
        """Тест параметра verbose_name у полей модели Comment"""
        verbose_names = {
            getattr(self.author_field, 'verbose_name'): 'Автор',
            getattr(self.post_field, 'verbose_name'): 'Пост',
            getattr(self.text_field, 'verbose_name'): 'Текст комментария',
        }
        for real_verbose_name, expected_verbose_name in verbose_names.items():
            with self.subTest(real_verbose_name=real_verbose_name):
                self.assertEqual(real_verbose_name, expected_verbose_name)
