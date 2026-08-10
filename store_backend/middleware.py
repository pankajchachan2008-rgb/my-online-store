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
        
        # 🌟 ULTIMATE CSP POLICY (Whitelisting all Service Worker fetch targets, media, scripts & styles)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://static.cloudflareinsights.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "img-src 'self' data: https://res.cloudinary.com https://images.unsplash.com; "
            "media-src 'self' https://res.cloudinary.com; "
            "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com; "
            "connect-src 'self' https://api.brevo.com https://www.cgsmart.in https://res.cloudinary.com https://cdn.jsdelivr.net; "
            "frame-src 'self' https://www.google.com; "
            "worker-src 'self'; "
            "frame-ancestors 'none';"
        )
        response['Content-Security-Policy'] = csp_policy
        return response