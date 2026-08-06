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
        # Disable strict browser CSP headers completely for AJAX and Cart to work
        if 'Content-Security-Policy' in response:
            del response['Content-Security-Policy']
        return response