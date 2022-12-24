import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache

from ..models import Group, Post, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()
MAX_POSTS_ON_PAGE = 10


class PostsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.author_2 = User.objects.create_user(username='TestAuthor_2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.post_2 = Post.objects.create(
            author=cls.author_2,
            text='Тестовый пост 2',
            group=cls.group_2,
            image=cls.uploaded,
        )
        cls.post_with_group_2 = Post.objects.create(
            author=cls.author,
            text='Тестовый пост с группой 2',
            group=cls.group,
        )
        cls.post_with_group = Post.objects.create(
            author=cls.author,
            text='Тестовый пост с группой',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            author=cls.author,
            post=cls.post_with_group,
            text='Тестовый комментарий'
        )
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)

    def setUp(cls):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_post', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:index'))
        all_objects = response.context['page_obj']
        first_object = all_objects[0]
        first_object_values = {
            first_object.text: self.post_with_group.text,
            first_object.author: self.post_with_group.author,
            first_object.group: self.post_with_group.group,
            first_object.image: self.post_with_group.image,
        }
        for post_value, expected_value in first_object_values.items():
            with self.subTest(expected_value=expected_value):
                self.assertEqual(post_value, expected_value)
        required_objects = Post.objects.all()
        for post in required_objects:
            with self.subTest(post=post):
                response = self.assertIn(post, all_objects)

    def test_group_post_show_correct_context(self):
        """Шаблон group_post сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:group_post', kwargs={'slug': self.group.slug})
        )
        group_object = response.context['group']
        self.assertEqual(group_object, self.group)
        all_page_objects = response.context['page_obj']
        first_object = all_page_objects[0]
        first_object_values = {
            first_object.text: self.post_with_group.text,
            first_object.author: self.post_with_group.author,
            first_object.group: self.post_with_group.group,
            first_object.image: self.post_with_group.image,
        }
        for post_value, expected_value in first_object_values.items():
            with self.subTest(expected_value=expected_value):
                self.assertEqual(post_value, expected_value)
        required_objects = self.group.posts.all()
        for post in required_objects:
            with self.subTest(post=post):
                response = self.assertIn(post, all_page_objects)

    def test_cant_follow_yourself(self):
        """Пользватель не может подписываться на себя."""
        before_follow = self.author.follower.count()
        self.authorized_author.get(reverse(
            'posts:profile_follow', kwargs={'username': self.author}
        ))
        after_follow = self.author.follower.count()
        self.assertEqual(before_follow, after_follow)

    def test_follow_index_before_follow(self):
        """Шаблон follow_index сформирован с правильным контекстом.
        При отсутствии подписок не выводит посты."""
        response = self.authorized_author.get(reverse('posts:follow_index'))
        all_objects = response.context['page_obj']
        self.assertEqual(len(all_objects), 0)

    def test_follow_index_after_follow(self):
        """Шаблон follow_index сформирован с правильным контекстом.
        При наличии подписок выводят связанные посты."""
        self.authorized_author.get(reverse(
            'posts:profile_follow', kwargs={'username': self.author_2}
        ))
        response = self.authorized_author.get(reverse('posts:follow_index'))
        all_objects = response.context['page_obj']
        first_object = all_objects[0]
        first_object_values = {
            first_object.text: self.post_2.text,
            first_object.author: self.post_2.author,
            first_object.group: self.post_2.group,
            first_object.image: self.post_2.image,
        }
        for post_value, expected_value in first_object_values.items():
            with self.subTest(expected_value=expected_value):
                self.assertEqual(post_value, expected_value)

    def test_follow_index_after_follow_new_post(self):
        """Шаблон follow_index сформирован с правильным контекстом.
        При добавлении поста автором, на которого подписан пользователь,
        пост появляется в ленте подписок"""
        # проверка после создания нового поста
        post_3 = Post.objects.create(
            author=self.author_2,
            text='Тестовый пост 3',
            group=self.group,
        )
        self.authorized_author.get(reverse(
            'posts:profile_follow', kwargs={'username': self.author_2}
        ))
        response = self.authorized_author.get(reverse('posts:follow_index'))
        all_objects = response.context['page_obj']
        first_object = all_objects[0]
        first_object_values = {
            first_object.text: post_3.text,
            first_object.author: post_3.author,
            first_object.group: post_3.group,
            first_object.image: post_3.image,
        }
        for post_value, expected_value in first_object_values.items():
            with self.subTest(expected_value=expected_value):
                self.assertEqual(post_value, expected_value)

    def test_follow_index_after_unfolow(self):
        """Шаблон follow_index сформирован с правильным контекстом.
        При отсутствии подписок не выводит посты."""
        self.authorized_author.get(reverse(
            'posts:profile_follow', kwargs={'username': self.author_2}
        ))
        self.authorized_author.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.author_2}
        ))
        response = self.authorized_author.get(reverse('posts:follow_index'))
        all_objects = response.context['page_obj']
        self.assertEqual(len(all_objects), 0)

    def test_follow_index_after_unfolow_new_post(self):
        """Шаблон follow_index сформирован с правильным контекстом.
        При отсутствии подписок не выводит новые посты авторов,
        на которых нет подписки."""
        self.authorized_author.get(reverse(
            'posts:profile_follow', kwargs={'username': self.author_2}
        ))
        self.authorized_author.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.author_2}
        ))
        Post.objects.create(
            author=self.author_2,
            text='Тестовый пост 4',
            group=self.group_2,
        )
        response = self.authorized_author.get(reverse('posts:follow_index'))
        all_objects = response.context['page_obj']
        self.assertEqual(len(all_objects), 0)

    def test_group_post_doesnt_show_extra_context(self):
        """Шаблон group_post сформирован без лишнего контекста."""
        response = self.authorized_author.get(
            reverse('posts:group_post', kwargs={'slug': self.group_2.slug})
        )
        all_page_objects = response.context['page_obj']
        self.assertNotIn(self.post_with_group, all_page_objects)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:profile', kwargs={'username': self.author})
        )
        author_object = response.context['author']
        self.assertEqual(author_object, self.author)
        all_page_objects = response.context['page_obj']
        first_object = all_page_objects[0]
        first_object_values = {
            first_object.text: self.post_with_group.text,
            first_object.author: self.post_with_group.author,
            first_object.group: self.post_with_group.group,
            first_object.image: self.post_with_group.image,
        }
        for post_value, expected_value in first_object_values.items():
            with self.subTest(expected_value=expected_value):
                self.assertEqual(post_value, expected_value)
        required_objects = self.author.posts.all()
        for post in required_objects:
            with self.subTest(post=post):
                response = self.assertIn(post, all_page_objects)

    def test_profile_doesnt_show_extra_context(self):
        """Шаблон profile сформирован без лишнего контекста."""
        response = self.authorized_author.get(
            reverse('posts:profile', kwargs={'username': self.author_2})
        )
        all_page_objects = response.context['page_obj']
        self.assertNotIn(self.post_with_group, all_page_objects)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post_with_group.id})
        )
        object = response.context['post']
        post_values = {
            object.text: self.post_with_group.text,
            object.author: self.post_with_group.author,
            object.group: self.post_with_group.group,
            object.image: self.post_with_group.image,
        }
        for post_value, expected_value in post_values.items():
            with self.subTest(expected_value=expected_value):
                self.assertEqual(post_value, expected_value)

    def test_post_detail_show_correct_comments(self):
        """Шаблон post_detail сформирован с правильной секцией комментариев."""
        response = self.authorized_author.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post_with_group.id})
        )
        object_form = response.context['form']
        object_comments = response.context['comments']
        self.assertIsInstance(
            object_form.fields['text'], forms.fields.CharField)
        self.assertEqual(
            len(object_comments), self.post_with_group.comments.count())

    def test_post_detail_adds_comment(self):
        """После успешной отправки комментарий появляется на странице поста."""
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_author.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        object = response.context['comments'][0]
        self.assertEqual(object.text, form_data['text'])

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:post_create')
        )
        self.assertNotIn('is_edit', response.context)
        object = response.context['form']
        form_instances = {
            object.fields['text']: forms.fields.CharField,
            object.fields['group']: forms.fields.ChoiceField,
        }
        for form_value in form_instances.keys():
            with self.subTest(form_value=form_value):
                self.assertIsNone(form_value.initial)
        for form_value, expected_value in form_instances.items():
            with self.subTest(form_value=form_value):
                self.assertIsInstance(form_value, expected_value)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post_with_group.id})
        )
        object_is_edit = response.context['is_edit']
        self.assertTrue(object_is_edit)
        object = response.context['form']
        form_values = {
            object['text'].value(): self.post_with_group.text,
            object['group'].value(): self.post_with_group.group.id
        }
        for form_value, expected_value in form_values.items():
            with self.subTest(form_value=form_value):
                self.assertEqual(form_value, expected_value)
        form_instances = {
            object.fields['text']: forms.fields.CharField,
            object.fields['group']: forms.fields.ChoiceField,
        }
        for form_value, expected_value in form_instances.items():
            with self.subTest(form_value=form_value):
                self.assertIsInstance(form_value, expected_value)

    # ТЕСТ КЭША У МЕНЯ ТУТ
    def test_index_cache(self):
        """Шаблон index правильно использует кэширование."""
        response = self.authorized_author.get(reverse('posts:index'))
        all_objects = response.content
        Post.objects.all().delete()
        response = self.authorized_author.get(reverse('posts:index'))
        all_objects_after_delate = response.content
        self.assertEqual(all_objects, all_objects_after_delate)
        cache.clear()
        response = self.authorized_author.get(reverse('posts:index'))
        all_objects_after_delate = response.content
        self.assertNotEqual(all_objects, all_objects_after_delate)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = []
        POSTS_CHECK_AMOUNT = 15
        for i in range(1, POSTS_CHECK_AMOUNT):
            new_post = Post(
                author=cls.author,
                group=cls.group,
            )
            cls.posts.append(new_post)
        cls.new_posts = Post.objects.bulk_create(cls.posts)
        cls.posts_on_last_page = Post.objects.count() % MAX_POSTS_ON_PAGE
        if cls.posts_on_last_page == 0:
            cls.posts_on_last_page = 10
        cls.last_page_number = Post.objects.count() // MAX_POSTS_ON_PAGE + 1

    def setUp(cls):
        cache.clear()

    def test_index_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), MAX_POSTS_ON_PAGE)

    def test_index_last_page_contains_right_amount_records(self):
        response = self.client.get(reverse(
            'posts:index'
        ) + f'?page={self.last_page_number}')
        self.assertEqual(
            len(response.context['page_obj']), self.posts_on_last_page)

    def test_group_post_first_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:group_post', kwargs={'slug': self.group.slug}))
        self.assertEqual(
            len(response.context['page_obj']), MAX_POSTS_ON_PAGE)

    def test_group_post_last_page_contains_right_amount_records(self):
        response = self.client.get(reverse(
            'posts:group_post', kwargs={'slug': self.group.slug}
        ) + f'?page={self.last_page_number}')
        self.assertEqual(
            len(response.context['page_obj']), self.posts_on_last_page)

    def test_profile_first_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.author}))
        self.assertEqual(
            len(response.context['page_obj']), MAX_POSTS_ON_PAGE)

    def test_profile_last_page_contains_right_amount_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.author}
        ) + f'?page={self.last_page_number}')
        self.assertEqual(
            len(response.context['page_obj']), self.posts_on_last_page)

    # тест кэша находится в конце пролого класса
