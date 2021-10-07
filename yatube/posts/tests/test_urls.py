from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        # неавторизованный клиент
        self.guest_client = Client()
        # авторизованный клиент автор
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        # авторизованный клиент
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_urls_exists(self):
        """Страницы доступны."""
        # открытые страницы
        open_urls_names = [
            reverse('posts:index'),
            reverse('posts:group_list', args={self.group.slug}),
            reverse('posts:profile', args={self.author.username}),
            reverse('posts:post_detail', args={self.post.pk}),
        ]
        for reverse_name in open_urls_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        # только авторизованному
        response = self.authorized_user.get(
            reverse('posts:post_create')
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # только автору
        response = self.authorized_author.get(
            reverse('posts:post_edit', args={self.post.pk})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_404(self):
        """Несуществующая страница отвечает 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_redirect(self):
        """Страницы правильно перенаправляют."""
        # редирект неавторизованного
        urls_names = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', args={self.post.pk}),
        ]
        for reverse_name in urls_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name, follow=True)
                self.assertRedirects(
                    response, (
                        reverse('users:login') + f'?next={reverse_name}'
                    )
                )
        # редирект не автора
        response = self.authorized_user.get(
            reverse('posts:post_edit', args={self.post.pk}), follow=True
        )
        self.assertRedirects(
            response, (
                reverse('posts:post_detail', args={self.post.pk})
            )
        )

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
            reverse('posts:group_list', args={self.group.slug}):
                'posts/group_list.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in url_templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)
