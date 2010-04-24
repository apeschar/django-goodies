import random
import datetime

class UniqueCookieMiddleware(object):
    KEY_LENGTH = 80
    KEY_CHARACTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890~!@#$%^&*()_+-={}[]:;<>?,./'
    COOKIE_NAME = 'token'

    def generate_key(self):
        key = ''
        for i in range(self.KEY_LENGTH):
            key += random.choice(self.KEY_CHARACTERS)
        return key

    def validate_key(self, key):
        if len(key) != self.KEY_LENGTH:
            raise ValueError, 'invalid key length'
        for x in key:
            if x not in self.KEY_CHARACTERS:
                raise ValueError, 'invalid character in key'

    def process_request(self, request):
        try:
            self.validate_key(request.COOKIES[self.COOKIE_NAME])
        except (KeyError, ValueError):
            request.unique_cookie = self.generate_key()
        else:
            request.unique_cookie = request.COOKIES[self.COOKIE_NAME]

    def process_response(self, request, response):
        try:
            key = request.unique_cookie
        except AttributeError:
            key = self.generate_key()
        expire_at = (datetime.datetime.utcnow() + datetime.timedelta(days=5*365)) \
                    .strftime('%a, %m-%b-%Y %H:%M:%S GMT')
        response.set_cookie(self.COOKIE_NAME, key, max_age=86400*365*5, expires=expire_at)
        return response
