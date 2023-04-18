from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import Permission

## get list of URLs that can be opened by non authenticated user

# Check if settings.py file has LOGIN_URL settings (exact path to login page)
EXEMPT_URLS = [settings.LOGIN_URL.lstrip('/')]

# If there is LOGIN_EXEMPT_URLS (urls that can be opened by unauth user) - add it to the list
if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
    EXEMPT_URLS += [url for url in settings.LOGIN_EXEMPT_URLS]

# redirect to login page if a user is not authenticated
class AuthRequiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        path = request.path_info.lstrip('/')
        if request.user.is_authenticated:
            user = request.user
            cache.set('_cached_user', user)
# To check users permissions
       #     permissions = Permission.objects.filter(user=request.user)
       #     print(permissions)
            return
        else:
            if path not in EXEMPT_URLS:
                return redirect('login')
            #    return HttpResponseRedirect(reverse('login'))

