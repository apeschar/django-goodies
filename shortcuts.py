from django.http import HttpResponseRedirect

def redirect(to):
    return HttpResponseRedirect(to)

def reverse(to, *args, **kwargs):
    from django.core.urlresolvers import reverse as _reverse
    return _reverse(to, args=args, kwargs=kwargs)

