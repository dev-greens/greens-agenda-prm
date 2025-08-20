from django.conf import settings
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

EXEMPT_PREFIXES = ('static/', 'media/')

class LoginRequiredMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip if authenticated
        if getattr(request, 'user', None) and request.user.is_authenticated:
            return None

        path = request.path.strip('/')

        # Exempt paths
        if not path:  # homepage allowed for redirect to login
            return None
        if path.startswith('admin/login') or path.startswith('admin/'):
            return None
        if path.startswith('accounts/'):
            return None
        if any(path.startswith(p) for p in EXEMPT_PREFIXES):
            return None
        if path.startswith('health'):
            return None

        # Enforce login
        login_url = settings.LOGIN_URL or '/accounts/login/'
        return redirect(f"{login_url}?next=/{path}")
