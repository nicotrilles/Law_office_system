from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from . import throttle

GENERIC_LOGIN_ERROR = "The username or password is incorrect."
UNAVAILABLE_ERROR = "Sign-in is temporarily unavailable. Please contact the system administrator."


def locked_error():
    minutes = settings.LOGIN_LOCKOUT_MINUTES
    unit = "minute" if minutes == 1 else "minutes"
    return f"Too many failed sign-in attempts. Please wait {minutes} {unit} and try again."


class LoginForm(AuthenticationForm):
    """Django's login form with ONE message for every failure, plus failed-attempt throttling.

    A wrong password, an unknown username, and a deactivated account all show the same text, so the
    page never reveals which usernames exist. (Django's own text also wrongly says usernames are
    case-sensitive; ours are not.) The lock message is the same for every username, real or not.
    """

    error_messages = {
        "invalid_login": GENERIC_LOGIN_ERROR,
        "inactive": GENERIC_LOGIN_ERROR,
    }

    def clean(self):
        username = self.cleaned_data.get("username")
        if username is None or not self.cleaned_data.get("password"):
            return super().clean()  # required-field errors only; nothing to count
        address = throttle.client_address(self.request)
        try:
            if throttle.is_locked(username, address):
                raise ValidationError(locked_error(), code="locked")  # password is NOT checked
            try:
                cleaned = super().clean()
            except ValidationError:
                throttle.record_failure(username, address)
                raise
            throttle.clear(username, address)
            return cleaned
        except throttle.ThrottleUnavailable:
            raise ValidationError(UNAVAILABLE_ERROR, code="unavailable")  # fail closed
