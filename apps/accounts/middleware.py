from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse


class LoginAttemptLimitMiddleware:
    """Bloqueia tentativas de login após N falhas por IP (RNF005)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == settings.LOGIN_URL and request.method == 'POST':
            ip = request.META.get('REMOTE_ADDR', 'unknown')
            cache_key = f'login_attempts_{ip}'
            attempts = cache.get(cache_key, 0)
            limit = getattr(settings, 'LOGIN_ATTEMPT_LIMIT', 10)
            window = getattr(settings, 'LOGIN_ATTEMPT_WINDOW_SECONDS', 600)

            if attempts >= limit:
                return HttpResponse(
                    'Muitas tentativas de login. Tente novamente em alguns minutos.',
                    status=429,
                )

            response = self.get_response(request)

            if response.status_code == 200 and b'errorlist' in getattr(response, 'content', b''):
                cache.set(cache_key, attempts + 1, timeout=window)
            elif response.status_code in (301, 302):
                cache.delete(cache_key)

            return response

        return self.get_response(request)
