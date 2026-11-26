"""permission_required: redirects, 403, 503, the 403 handler, and route protection."""
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.db.utils import OperationalError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import get_resolver, reverse
from django.urls.resolvers import URLResolver

from apps.accounts import permissions, reference_data
from apps.accounts.decorators import permission_required
from apps.accounts.models import Permission, Role, RolePermission, User
from apps.accounts.tests import urls_for_tests
from apps.core.views import permission_denied

PASSWORD = "correct-horse-battery-staple"
LOGIN = "/accounts/login/"


def apply_initial_matrix(staff_role, attorney_role):
    """The confirmed matrix: Office Staff holds all three, the Attorney holds client.view only."""
    for key in ("client.view", "client.create", "client.edit"):
        RolePermission.objects.create(role=staff_role, permission=Permission.objects.get(permission_key=key))
    RolePermission.objects.create(role=attorney_role, permission=Permission.objects.get(permission_key="client.view"))


@override_settings(ROOT_URLCONF="apps.accounts.tests.urls_for_tests")
class DecoratorTests(TestCase):
    def setUp(self):
        reference_data.sync_roles()
        reference_data.sync_permissions()
        self.staff_role = Role.objects.get(role_name="Office Staff")
        self.attorney_role = Role.objects.get(role_name="Attorney")
        apply_initial_matrix(self.staff_role, self.attorney_role)
        self.staff = User.objects.create_user("staffer", "Sam Staff", self.staff_role, PASSWORD)
        self.attorney = User.objects.create_user("attorney1", "Atty Jumamil", self.attorney_role, PASSWORD)
        clerk_role = Role.objects.create(role_name="Clerk")  # a role that holds nothing
        self.nobody = User.objects.create_user("nobody1", "No Permissions", clerk_role, PASSWORD)
        urls_for_tests.calls.clear()

    # ---- anonymous visitors ----
    def test_anonymous_get_is_redirected_to_sign_in_and_the_view_does_not_run(self):
        response = self.client.get("/test/clients/")
        self.assertRedirects(response, f"{LOGIN}?next=/test/clients/", fetch_redirect_response=False)
        self.assertEqual(urls_for_tests.calls, [])

    def test_anonymous_post_is_redirected_to_sign_in_and_the_view_does_not_run(self):
        response = self.client.post("/test/clients/new/")
        self.assertRedirects(response, f"{LOGIN}?next=/test/clients/new/", fetch_redirect_response=False)
        self.assertEqual(urls_for_tests.calls, [])

    def test_an_inactive_users_existing_session_is_treated_as_signed_out(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/test/clients/").status_code, 200)
        User.objects.filter(pk=self.staff.pk).update(account_status="inactive")
        response = self.client.get("/test/clients/")
        self.assertRedirects(response, f"{LOGIN}?next=/test/clients/", fetch_redirect_response=False)  # not a 403

    # ---- allowed ----
    def test_a_user_who_holds_the_permission_is_allowed_on_get_and_post(self):
        self.client.force_login(self.staff)
        self.assertContains(self.client.get("/test/clients/"), "clients page")
        self.assertContains(self.client.get("/test/clients/new/"), "create form")
        self.assertContains(self.client.post("/test/clients/new/"), "created")
        self.assertEqual(urls_for_tests.calls, [("view", "GET"), ("create", "GET"), ("create", "POST")])

    # ---- denied (403) ----
    def test_the_attorney_may_view_but_not_create_under_the_confirmed_matrix(self):
        self.client.force_login(self.attorney)
        self.assertEqual(self.client.get("/test/clients/").status_code, 200)
        urls_for_tests.calls.clear()
        self.assertEqual(self.client.get("/test/clients/new/").status_code, 403)
        self.assertEqual(self.client.post("/test/clients/new/").status_code, 403)
        self.assertEqual(urls_for_tests.calls, [])  # the refused view never ran

    def test_a_signed_in_user_without_the_permission_gets_the_generic_403_page(self):
        self.client.force_login(self.nobody)
        for method in (self.client.get, self.client.post):
            response = method("/test/clients/")
            self.assertEqual(response.status_code, 403)
            self.assertTemplateUsed(response, "errors/403.html")
            self.assertContains(response, "Access denied", status_code=403)
            self.assertNotContains(response, "client.view", status_code=403)  # no permission names leak
        self.assertEqual(urls_for_tests.calls, [])

    def test_a_denial_is_logged_with_the_user_id_and_permission_but_no_username(self):
        self.client.force_login(self.nobody)
        with self.assertLogs("apps.accounts.decorators", level="WARNING") as logs:
            self.client.get("/test/clients/")
        text = " ".join(logs.output)
        self.assertIn(f"user_id={self.nobody.pk}", text)
        self.assertIn("permission=client.view", text)
        self.assertNotIn("nobody1", text)

    def test_typing_a_protected_address_by_hand_gives_403_and_an_unknown_address_gives_404(self):
        self.client.force_login(self.nobody)
        self.assertEqual(self.client.get("/test/clients/new/").status_code, 403)
        self.assertEqual(self.client.get("/test/no-such-page/").status_code, 404)

    def test_grants_and_revokes_apply_to_the_very_next_request(self):
        self.client.force_login(self.nobody)
        self.assertEqual(self.client.get("/test/clients/").status_code, 403)
        permission = Permission.objects.get(permission_key="client.view")
        row = RolePermission.objects.create(role=self.nobody.role, permission=permission)
        self.assertEqual(self.client.get("/test/clients/").status_code, 200)
        row.delete()
        self.assertEqual(self.client.get("/test/clients/").status_code, 403)

    # ---- the 403 handler itself ----
    def test_the_403_handler_returns_a_generic_page_directly(self):
        response = permission_denied(RequestFactory().get("/anything/"))
        self.assertEqual(response.status_code, 403)
        self.assertIn("Access denied", response.content.decode())

    # ---- lookup failure: 503, never 403, never a grant ----
    def test_a_lookup_failure_gives_503_not_403_and_the_view_does_not_run(self):
        self.client.force_login(self.staff)
        with mock.patch.object(permissions, "_load_keys", side_effect=OperationalError("relation does not exist")):
            with self.assertLogs("apps.accounts.permissions", level="ERROR"):
                response = self.client.get("/test/clients/")
        self.assertEqual(response.status_code, 503)
        self.assertNotEqual(response.status_code, 403)  # 403 is reserved for a genuine denial
        self.assertTemplateUsed(response, "errors/503.html")
        self.assertContains(response, "Temporarily unavailable", status_code=503)
        for leak in ("OperationalError", "relation does not exist", "client.view"):
            self.assertNotContains(response, leak, status_code=503)
        self.assertEqual(urls_for_tests.calls, [])

    def test_a_lookup_failure_never_lets_a_user_in_even_if_they_hold_the_permission(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/test/clients/").status_code, 200)  # holds it normally
        with mock.patch.object(permissions, "_load_keys", side_effect=OperationalError("x")):
            with self.assertLogs("apps.accounts.permissions", level="ERROR"):
                self.assertEqual(self.client.post("/test/clients/new/").status_code, 503)

    def test_anonymous_visitors_are_still_redirected_during_a_lookup_failure(self):
        with mock.patch.object(permissions, "_load_keys", side_effect=OperationalError("x")):
            response = self.client.get("/test/clients/")
        self.assertEqual(response.status_code, 302)

    # ---- the decorator itself ----
    def test_a_misspelt_key_fails_when_the_decorator_is_applied(self):
        with self.assertRaises(ImproperlyConfigured):
            permission_required("client.vew")

    def test_the_decorator_keeps_the_view_name(self):
        self.assertEqual(urls_for_tests.clients_page.__name__, "clients_page")


def named_routes(resolver, prefix=""):
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            yield from named_routes(pattern, prefix + (f"{pattern.namespace}:" if pattern.namespace else ""))
        elif pattern.name:
            yield prefix + pattern.name


class RouteProtectionTests(TestCase):
    """Default-deny inventory of the REAL application routes (config/urls.py).

    Any route added later must either require sign-in or be added to PUBLIC on purpose.
    """

    PUBLIC = {"health", "accounts:login", "accounts:logout"}

    def test_every_route_outside_the_public_list_redirects_anonymous_visitors_to_sign_in(self):
        names = set(named_routes(get_resolver()))
        self.assertIn("home", names)
        self.assertTrue(self.PUBLIC <= names, "the public list names routes that do not exist")
        for name in sorted(names - self.PUBLIC):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertTrue(response["Location"].startswith(reverse("accounts:login")), name)

    def test_the_public_routes_are_public_on_purpose(self):
        self.assertEqual(self.client.get(reverse("health")).status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)  # POST only

    def test_the_home_page_needs_sign_in_only_not_a_permission(self):
        reference_data.sync_roles()
        reference_data.sync_permissions()  # definitions exist, but nothing is assigned to anyone
        for role_name in ("Office Staff", "Attorney"):
            user = User.objects.create_user(role_name.replace(" ", "").lower(), "A Person",
                                            Role.objects.get(role_name=role_name), PASSWORD)
            self.client.force_login(user)
            self.assertEqual(self.client.get("/").status_code, 200, role_name)
