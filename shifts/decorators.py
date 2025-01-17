from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func