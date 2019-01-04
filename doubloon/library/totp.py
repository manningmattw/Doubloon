from django.contrib.auth.models import User
from django.shortcuts import HttpResponseRedirect
from pyotp import TOTP
from . import credentials


class Backend(object):
    def authenticate(self, request, username=None, password=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        totp = TOTP(credentials.Credentials().totp_secret)

        if user.username == username and totp.verify(password):
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class AuthRequiredMiddleware(object):
    def process_request(self, request):
        if not request.user.is_authenticated():
            return HttpResponseRedirect('admin/login/')

        return None
