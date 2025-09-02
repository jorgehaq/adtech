from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class TenantIsolationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            auth = JWTAuthentication()
            try:
                validated_token = auth.get_validated_token(self.get_token_from_request(request))
                user = auth.get_user(validated_token)
                request.user = user
                request.tenant_id = (
                    user.tenant_id if hasattr(user, 'tenant_id') else None
                )
            except (InvalidToken, AttributeError):
                pass

        response = self.get_response(request)
        return response

    def get_token_from_request(self, request):
        header = request.META.get('HTTP_AUTHORIZATION')
        if header and header.startswith('Bearer '):
            return header.split(' ')[1].encode('utf-8')
        return None
