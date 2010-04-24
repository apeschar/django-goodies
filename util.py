import string
import random

def generate_password(length=8, chars=None):
    if chars is None:
        chars = string.letters + string.digits
    return ''.join([random.choice(chars) for i in range(length)])
