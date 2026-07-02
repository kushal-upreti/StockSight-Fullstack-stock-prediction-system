from io import BytesIO
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProfilePictureUploadTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='stockuser',
            email='stockuser@example.com',
            password='testpass123',
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.url = reverse('profile-picture')

    def test_user_can_upload_profile_picture(self):
        image = SimpleUploadedFile(
            'avatar.png',
            self._png_bytes(),
            content_type='image/png',
        )

        response = self.client.put(self.url, {'profile_picture': image}, format='multipart')

        self.assertEqual(response.status_code, 200)
        self.assertIn('profile_picture_url', response.data)
        self.assertTrue(response.data['profile_picture'].endswith('.png'))
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.profile_picture.name.startswith('profile_pics/'))

    def test_user_can_delete_profile_picture(self):
        image = SimpleUploadedFile(
            'avatar.png',
            self._png_bytes(),
            content_type='image/png',
        )
        self.client.put(self.url, {'profile_picture': image}, format='multipart')

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['profile_picture_url'])
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.profile_picture)

    def test_upload_rejects_non_image_file(self):
        file_upload = SimpleUploadedFile(
            'notes.txt',
            b'not an image',
            content_type='text/plain',
        )

        response = self.client.put(self.url, {'profile_picture': file_upload}, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertIn('profile_picture', response.data)

    def _png_bytes(self):
        file_obj = BytesIO()
        Image.new('RGB', (1, 1), color='white').save(file_obj, format='PNG')
        file_obj.seek(0)
        return file_obj.read()
