from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import LoginForm

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            form_class=LoginForm,                    # our form: one generic error message
            template_name="accounts/login.html",     # our page, not Django's registration/login.html
            redirect_authenticated_user=True,        # a signed-in visitor is sent onward
        ),
        name="login",
    ),
    # LogoutView accepts POST only (Django 5), so signing out needs a form with a CSRF token.
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
