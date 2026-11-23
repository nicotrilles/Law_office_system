"""Sign-in, sign-out, and protection of the home page."""
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.forms import LoginForm
from apps.accounts.models import Role, User

PASSWORD = "correct-horse-battery-staple"


class LoginTestCase(TestCase):
    def setUp(self):
        self.role = Role.objects.create(role_name="Office Staff")
        self.user = User.objects.create_user("maria", "Maria Santos", self.role, PASSWORD)
        self.login_url = reverse("accounts:login")

    def sign_in(self, username="maria", password=PASSWORD, next_url=None):
        data = {"username": username, "password": password}
        if next_url is not None:
            data["next"] = next_url
        return self.client.post(self.login_url, data)


class LoginPageTests(LoginTestCase):
    def test_login_page_uses_our_template_and_our_form(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertIsInstance(response.context["form"], LoginForm)

    def test_login_page_carries_a_csrf_token(self):
        self.assertContains(self.client.get(self.login_url), "csrfmiddlewaretoken")

    def test_a_signed_in_visitor_on_the_login_page_is_sent_onward(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(self.login_url), "/", fetch_redirect_response=False)


class SignInTests(LoginTestCase):
    def test_correct_credentials_sign_in_and_go_to_the_home_page(self):
        response = self.sign_in()
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertEqual(self.client.session["_auth_user_id"], str(self.user.pk))

    def test_username_works_in_any_letter_case(self):
        self.assertRedirects(self.sign_in(username="MARIA"), "/", fetch_redirect_response=False)

    def test_wrong_password_unknown_user_and_inactive_account_show_the_same_message(self):
        User.objects.create_user("inactive_ivan", "Ivan", self.role, PASSWORD)
        User.objects.filter(username="inactive_ivan").update(account_status="inactive")
        messages = []
        for username, password in (("maria", "wrong-password-123"), ("nobody", PASSWORD), ("inactive_ivan", PASSWORD)):
            client = Client()
            response = client.post(self.login_url, {"username": username, "password": password})
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("_auth_user_id", client.session)
            messages.append(list(response.context["form"].non_field_errors()))
        self.assertEqual(messages[0], ["The username or password is incorrect."])
        self.assertEqual(messages[0], messages[1])
        self.assertEqual(messages[0], messages[2])

    def test_a_failed_sign_in_does_not_echo_the_password(self):
        response = self.sign_in(password="Never-Show-This-1234")
        self.assertNotContains(response, "Never-Show-This-1234")

    def test_session_key_is_replaced_at_sign_in(self):
        session = self.client.session
        session["anything"] = 1
        session.save()
        key_before = self.client.session.session_key
        self.sign_in()
        self.assertNotEqual(self.client.session.session_key, key_before)

    def test_session_cookie_is_httponly_and_samesite_lax(self):
        self.sign_in()
        cookie = self.client.cookies[settings.SESSION_COOKIE_NAME]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_session_uses_the_configured_idle_timeout_and_ends_with_the_browser(self):
        self.sign_in()
        session = self.client.session
        self.assertEqual(session.get_expiry_age(), settings.SESSION_COOKIE_AGE)
        self.assertTrue(session.get_expire_at_browser_close())

    def test_sign_in_without_a_csrf_token_is_refused(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(self.login_url, {"username": "maria", "password": PASSWORD})
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("_auth_user_id", client.session)


class RedirectSafetyTests(LoginTestCase):
    def test_a_next_address_on_this_site_is_followed(self):
        self.assertRedirects(self.sign_in(next_url="/health/"), "/health/", fetch_redirect_response=False)

    def test_next_addresses_pointing_elsewhere_are_ignored(self):
        for evil in ("https://evil.example/", "//evil.example/"):
            self.client.logout()
            self.assertRedirects(self.sign_in(next_url=evil), "/", fetch_redirect_response=False)


class SignOutTests(LoginTestCase):
    def test_sign_out_by_get_is_refused(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_sign_out_by_post_ends_the_session(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, self.login_url, fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get("/").status_code, 302)

    def test_sign_out_without_a_csrf_token_is_refused(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse("accounts:logout")).status_code, 403)


class ProtectionTests(LoginTestCase):
    def test_anonymous_visitor_is_redirected_to_the_login_page(self):
        self.assertRedirects(self.client.get("/"), f"{self.login_url}?next=/", fetch_redirect_response=False)

    def test_signed_in_user_sees_the_home_page_with_name_and_sign_out_button(self):
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Maria Santos")
        self.assertContains(response, "Sign out")

    def test_a_deactivated_users_existing_session_stops_working(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/").status_code, 200)
        User.objects.filter(pk=self.user.pk).update(account_status="inactive")
        self.assertEqual(self.client.get("/").status_code, 302)

    def test_health_check_and_error_pages_stay_public(self):
        self.assertEqual(self.client.get("/health/").status_code, 200)
        self.assertEqual(self.client.get("/does-not-exist/").status_code, 404)
