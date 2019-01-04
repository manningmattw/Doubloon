# -*- coding: UTF-8 -*-
import os


class Credentials(object):
    @property
    def secretKey(self):
        return os.environ['secret_key']

    @property
    def totp_secret(self):
        return os.environ['totp_secret']

    @property
    def dbHost(self):
        return os.environ['db_host']

    @property
    def dbName(self):
        return os.environ['db_name']

    @property
    def dbUser(self):
        return os.environ['db_user']

    @property
    def dbPass(self):
        return os.environ['db_pass']

    @property
    def bittrexApiKey(self):
        return os.environ['bittrex_api_key']

    @property
    def bittrexApiSecret(self):
        return os.environ['bittrex_api_secret']
