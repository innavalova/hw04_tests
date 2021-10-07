from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from ..models import Group, Post

User = get_user_model()


class PostViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        # cls.user = User.objects.create_user(username='test_user')
        cls.groups = [
            Group.objects.create(
                title='Первая группа',
                slug='first',
                description='Описание первой группы',
            ),
            Group.objects.create(
                title='Вторая группа',
                slug='second',
                description='Описание второй группы',
            ),
        ]
        cls.group_1 = cls.groups[0]
        cls.group_2 = cls.groups[1]
        cls.posts = [
            Post.objects.create(
                text='Тестовый пост',
                author=cls.author,
                group=cls.group_1,
            ),
            Post.objects.create(
                text='Тестовый пост',
                author=cls.author,
                group=cls.group_2,
            ),
        ]
        cls.post_in_group = cls.posts[0]
        cls.post = cls.posts[1]

    def setUp(self):
        # неавторизованный клиент
        # self.guest_client = Client()
        # авторизованный клиент автор
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        # авторизованный клиент
        # self.authorized_user = Client()
        # self.authorized_user.force_login(self.user)

    def test_correct_template(self):
        """URL-адреса используют правильные шаблоны."""
        url_templates_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', args={self.author.username}):
                'posts/profile.html',
            reverse('posts:post_edit', args={self.post.pk}):
                'posts/create_post.html',
            reverse('posts:post_detail', args={self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:group_list', args={self.group_1.slug}):
                'posts/group_list.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in url_templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_list_context(self):
        """Шаблон получает правильное количество постов."""
        urls_posts = {
            reverse('posts:index'): len(self.posts),
            reverse('posts:profile', args={self.author.username}):
                self.author.posts.count(),
            # группы при необходимости тоже можно циклом внутри перебрать
            reverse('posts:group_list', args={self.group_1.slug}):
                self.group_1.posts.count(),
            reverse('posts:group_list', args={self.group_2.slug}):
                self.group_2.posts.count(),
        }
        for reverse_name, object in urls_posts.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertIn('posts', response.context)
                self.assertEqual(len(response.context['posts']), object)

    def test_post_context(self):
        """Шаблон получает посты с корректным содержимым."""
        urls = [
            reverse('posts:index'),
            reverse('posts:profile', args={self.author.username}),
            reverse('posts:group_list', args={self.group_1.slug}),
        ]
        for reverse_name in urls:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                first_object = response.context['posts'][0]
                post_text_0 = first_object.text
                print(post_text_0)
                print(self.post_in_group.text)
                post_author_0 = first_object.author.username
                post_group_0 = first_object.group.title
                self.assertEqual(post_text_0, self.post_in_group.text)
                self.assertEqual(post_author_0, self.author.username)
                self.assertEqual(post_group_0, self.group_1.title)

    def test_post_id_context(self):
        """Шаблон получает пост с корректным id."""
        response = self.authorized_author.get(
            reverse('posts:post_detail', args={self.post.pk})
        )
        post = response.context['post']
        self.assertEqual(post.pk, self.post.pk)

    def test_group_context(self):
        """Пост попадает в корректную группу."""
        response = self.authorized_author.get(
            reverse('posts:group_list', args={self.group_1.slug})
        )
        post = response.context['posts'][0]
        self.assertEqual(post.pk, self.post_in_group.pk)
        self.assertNotEqual(post.pk, self.post.pk)

    def test_form_context(self):
        """Шаблон получает корректные поля формы."""
        urls = [
            reverse('posts:post_edit', args={self.post.pk}),
            reverse('posts:post_create'),
        ]
        for reverse_name in urls:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value)
                        self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Описание группы',
        )
        number_of_posts = 13
        cls.posts = []
        for post_id in range(number_of_posts):
            post = Post.objects.create(
                text=f'Тестовый пост {post_id}',
                author=cls.author,
                group=cls.group,
            )
            cls.posts.append(post)
        cls.urls_with_paginator = [
            reverse('posts:index'),
            reverse('posts:profile', args={cls.author.username}),
            reverse('posts:group_list', args={cls.group.slug}),
        ]

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_first_page_contains_ten_records(self):
        """Количество постов на первой странице."""
        for reverse_name in self.urls_with_paginator:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Количество постов на второ странице."""
        for reverse_name in self.urls_with_paginator:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
