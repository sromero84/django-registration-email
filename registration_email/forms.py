"""Custom registration forms that expects an email address as a username."""
import hashlib
import os

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _


# I put this on all required fields, because it's easier to pick up
# on them with CSS or JavaScript if they have a class of "required"
# in the HTML. Your mileage may vary. If/when Django ticket #3515
# lands in trunk, this will no longer be necessary.
attrs_dict = {'class': 'required'}

USER = get_user_model()

def get_md5_hexdigest(email):
    """
    Returns an md5 hash for a given email.

    The length is 30 so that it fits into Django's ``User.username`` field.

    """
    return hashlib.md5(email).hexdigest()[0:30]


def generate_username(email):
    """
    Generates a unique username for the given email.

    The username will be an md5 hash of the given email. If the username exists
    we just append `a` to the email until we get a unique md5 hash.

    """
    try:
        USER.objects.get(email=email)
        raise Exception('Cannot generate new username. A user with this email'
                        'already exists.')
    except USER.DoesNotExist:
        pass

    username = get_md5_hexdigest(email)
    found_unique_username = False
    while not found_unique_username:
        try:
            USER.objects.get(username=username)
            email = '{0}a'.format(email.lower())
            username = get_md5_hexdigest(email)
        except USER.DoesNotExist:
            found_unique_username = True
            return username


class EmailAuthenticationForm(AuthenticationForm):
    remember_me = forms.BooleanField(
        required=False,
        label=_('Remember me'),
    )

    def __init__(self, *args, **kwargs):
        super(EmailAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields['username'] = forms.CharField(
            label=_("Email"), max_length=256)

    def clean_username(self):
        """Prevent case-sensitive erros in email/username."""
        return self.cleaned_data['username'].lower()


class EmailRegistrationForm(forms.Form):
    """
    Form for registering a new user account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """
    email = forms.EmailField(
        widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=256)),
        label=_("Email")
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
        label=_("Password")
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
        label=_("Password (repeat)"))
    your_name = forms.CharField(required=False)

    def clean_email(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.

        """
        email = self.cleaned_data['email'].strip()
        try:
            USER.objects.get(email__iexact=email)
        except USER.DoesNotExist:
            return email.lower()
        raise forms.ValidationError(
            _('A user with that email already exists.'))

    def clean(self):
        """
        Verifiy that the values entered into the two password fields match.

        Note that an error here will end up in ``non_field_errors()`` because
        it doesn't apply to a single field.

        """
        data = self.cleaned_data
        if data.get('your_name'):
            # Bot protection. The name field is not visible for human users.
            raise forms.ValidationError(_('Please enter a valid name.'))
        if not 'email' in data:
            return data
        if ('password1' in data and 'password2' in data):

            if data['password1'] != data['password2']:
                raise forms.ValidationError(
                    _("The two password fields didn't match."))
        try:
            # Set username only if neccesary
            USER._meta.get_field('username')
            self.cleaned_data['username'] = generate_username(data['email'])
        except USER.FieldDoesNotExist:
            pass
        return self.cleaned_data

    class Media:
        css = {
            'all': (os.path.join(
                settings.STATIC_URL, 'registration_email/css/auth.css'), )
        }
