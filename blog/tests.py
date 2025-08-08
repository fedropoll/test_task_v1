from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Post, SubPost
from django.db.models import F
import json

class BlogAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.admin_user = User.objects.create_user(username='adminuser', password='adminpassword', is_staff=True, is_superuser=True)

        response = self.client.post(reverse('token_obtain_pair'), {'username': 'testuser', 'password': 'testpassword'})
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        self.post1 = Post.objects.create(title='Post 1', body='Body 1', author=self.user)
        self.post2 = Post.objects.create(title='Post 2', body='Body 2', author=self.user)

        self.subpost1_1 = SubPost.objects.create(title='SubPost 1.1', body='SubBody 1.1', post=self.post1)
        self.subpost1_2 = SubPost.objects.create(title='SubPost 1.2', body='SubBody 1.2', post=self.post1)

    def test_post_list_creation_authenticated(self):
        data = {'title': 'New Post', 'body': 'New Body', 'author': self.user.id}
        response = self.client.post(reverse('post-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 3)
        self.assertEqual(Post.objects.last().title, 'New Post')

    def test_post_list_creation_unauthenticated(self):
        self.client.credentials()
        data = {'title': 'New Post', 'body': 'New Body', 'author': self.user.id}
        response = self.client.post(reverse('post-list'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_detail_retrieval(self):
        response = self.client.get(reverse('post-detail', args=[self.post1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.post1.title)
        self.assertIn('subposts', response.data)

    def test_post_update(self):
        data = {'title': 'Updated Post Title'}
        response = self.client.patch(reverse('post-detail', args=[self.post1.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Updated Post Title')

    def test_post_deletion(self):
        response = self.client.delete(reverse('post-detail', args=[self.post1.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 1)

    def test_subpost_list_creation(self):
        data = {'title': 'New SubPost', 'body': 'New SubBody', 'post': self.post2.id}
        response = self.client.post(reverse('subpost-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SubPost.objects.count(), 3)

    def test_subpost_detail_retrieval(self):
        response = self.client.get(reverse('subpost-detail', args=[self.subpost1_1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.subpost1_1.title)

    def test_subpost_update(self):
        data = {'body': 'Updated SubBody'}
        response = self.client.patch(reverse('subpost-detail', args=[self.subpost1_1.id]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subpost1_1.refresh_from_db()
        self.assertEqual(self.subpost1_1.body, 'Updated SubBody')

    def test_subpost_deletion(self):
        response = self.client.delete(reverse('subpost-detail', args=[self.subpost1_1.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SubPost.objects.count(), 1)

    def test_bulk_post_creation(self):
        data = [
            {'title': 'Bulk Post 1', 'body': 'Bulk Body 1'},
            {'title': 'Bulk Post 2', 'body': 'Bulk Body 2'}
        ]
        response = self.client.post(reverse('bulk_create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 4)
        self.assertTrue(Post.objects.filter(title='Bulk Post 1').exists())
        self.assertTrue(Post.objects.filter(title='Bulk Post 2').exists())

    def test_nested_subpost_creation_on_post_create(self):
        data = {
            'title': 'Post with Nested SubPosts',
            'body': 'Body of nested post',
            'author': self.user.id,
            'subposts': [
                {'title': 'Nested SubPost 1', 'body': 'Nested SubBody 1'},
                {'title': 'Nested SubPost 2', 'body': 'Nested SubBody 2'}
            ]
        }
        response = self.client.post(reverse('post-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_post = Post.objects.get(title='Post with Nested SubPosts')
        self.assertEqual(new_post.subposts.count(), 2)
        self.assertTrue(new_post.subposts.filter(title='Nested SubPost 1').exists())

    def test_nested_subpost_update_on_post_update(self):
        post = self.post1
        subpost_to_update = self.subpost1_1
        subpost_to_delete = self.subpost1_2

        data = {
            'title': 'Updated Post Title',
            'body': 'Updated Post Body',
            'subposts': [
                {'id': subpost_to_update.id, 'title': 'Updated SubPost 1.1', 'body': 'Updated SubBody 1.1'},
                {'title': 'New SubPost 1.3', 'body': 'New SubBody 1.3'}
            ]
        }
        response = self.client.patch(reverse('post-detail', args=[post.id]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        post.refresh_from_db()
        self.assertEqual(post.title, 'Updated Post Title')
        self.assertEqual(post.subposts.count(), 2)

        updated_subpost = SubPost.objects.get(id=subpost_to_update.id)
        self.assertEqual(updated_subpost.title, 'Updated SubPost 1.1')

        self.assertTrue(post.subposts.filter(title='New SubPost 1.3').exists())

        self.assertFalse(SubPost.objects.filter(id=subpost_to_delete.id).exists())

    def test_post_like_toggle(self):
        response = self.client.post(reverse('post-like', args=[self.post1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.likes.count(), 1)
        self.assertTrue(self.user in self.post1.likes.all())

        response = self.client.post(reverse('post-like', args=[self.post1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.likes.count(), 0)
        self.assertFalse(self.user in self.post1.likes.all())

        response = self.client.post(reverse('post-like', args=[self.post1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.likes.count(), 1)
        self.assertTrue(self.user in self.post1.likes.all())

    def test_post_view_increment_atomic(self):
        initial_views = self.post1.views_count
        num_requests = 10

        for _ in range(num_requests):
            self.client.get(reverse('post-view', args=[self.post1.id]))

        self.post1.refresh_from_db()
        self.assertEqual(self.post1.views_count, initial_views + num_requests)

        response = self.client.get(reverse('post-view', args=[self.post1.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('views_count', response.data)
        self.assertEqual(response.data['views_count'], initial_views + num_requests + 1)
