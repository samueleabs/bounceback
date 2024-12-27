class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "  # Allow scripts from self, unsafe-inline, unsafe-eval, and cdn.jsdelivr.net
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "  # Allow styles from self, unsafe-inline, cdn.jsdelivr.net, and fonts.googleapis.com
            "img-src 'self' data:; "  # Allow images from self and data URIs
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "  # Allow fonts from self, cdn.jsdelivr.net, and fonts.gstatic.com
        )
        return response