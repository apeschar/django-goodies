from django.http import HttpResponse
from django.utils import simplejson
from django.core.mail import mail_admins
from django.utils.translation import ugettext as _
import sys

def json_view(func):
    def wrap(request, *a, **kw):
        response = func(request, *a, **kw)
        assert isinstance(response, dict)
        response = dict(response)
        if 'result' not in response:
            response['result'] = 'ok'
        json = simplejson.dumps(response)
        return HttpResponse(json, mimetype='application/json')
    return wrap

