from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User

from db_util import DBUtil


class AuthBackend(BaseBackend):
    def __init__(self):
        self.db_util = DBUtil()

    def authenticate(self, request, username=None, password=None):
        if username and password:
            username = str(username).strip()
            password = str(password).strip()
            db_password = self.db_util.get_user_password(username)
            if db_password and db_password == password:
                user = User.objects.create_user(username, password=password)
                return user
        return None

    def get_user(self, user_id):
        _dummy_password = self.db_util.get_user_password(username=user_id)
        _dummy_password = _dummy_password.strip()
        if _dummy_password:
            user = User.objects.create_user(user_id)
            return user
        return None
