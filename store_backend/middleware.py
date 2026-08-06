from django.http import HttpResponseForbidden

BLOCKED_PATH_KEYWORDS = [
    '.php', 'wp-admin', 'wp-content', 'wp-includes', 
    'cgi-bin', 'manager.php', 'simple.php'
]

class BlockBadBotsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path.lower()
        if any(keyword in path for keyword in BLOCKED_PATH_KEYWORDS):
            return HttpResponseForbidden("Access Denied: Scanning is blocked.")
        return self.get_response(request)

class FixCSPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # 🌟 Sabhi restrictions ko hata kar sab kuch explicitly allow kar rahe hain
        response['Content-Security-Policy'] = (
            "default-src 'self' https: http: data: blob: 'unsafe-inline' 'unsafe-eval'; "
            "connect-src 'self' https: http: *; "
            "img-src 'self' https: http: data: blob: *; "
            "script-src 'self' https: http: 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' https: http: 'unsafe-inline';"
        )
        return response