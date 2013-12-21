"""
Custom authentication backends.

Inspired by http://djangosnippets.org/snippets/2463/

"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.validators import validate_email

USER = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows to login with an email address.

    """

    supports_object_permissions = True
    supports_anonymous_user = False
    supports_inactive_user = False

    def authenticate(self, username=None, password=None):
        try:
            validate_email(username)
        except:
            username_is_email = False
        else:
            username_is_email = True
        if username_is_email:
            try:
                user = USER.objects.get(email=username)
            except USER.DoesNotExist:
                return None
        else:
            #We have a non-email address username we should try username
            try:
                user = USER.objects.get(username=username)
            except USER.DoesNotExist:
                return None
        if USER.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return USER.objects.get(pk=user_id)
        except USER.DoesNotExist:
            return None
