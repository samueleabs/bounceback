# filepath: /C:/Users/samue/Desktop/projects/bounceback/shifts/csp_middleware.py
class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = "script-src 'self' 'unsafe-eval';"
        return response