from django.test import Client, RequestFactory, TestCase
from django.contrib.auth.models import AnonymousUser, User

class LoginTest(TestCase):

    def test_login_available(self):
        client = Client()
        response = client.get('/')
        self.assertEqual(response.status_code, 302)

        response = client.get('/', follow=True)
        self.assertNotEqual(response.redirect_chain, [])

        response = client.get(response.redirect_chain[0][0])
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        user = User.objects.create_user(
            username='usertest', email='usermail@…', password='userpswd',
            is_superuser=True)

        client = Client()
        response = client.get('/accounts/login/')
        client.force_login(user)

        response = client.get('/')
        self.assertEqual(response.status_code, 200)

        client.logout()
