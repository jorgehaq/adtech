from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class TenantIsolationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Excluir rutas de auth
        auth_excluded_paths = [
            '/api/v1/auth/register/',
            '/api/v1/auth/login/',
            '/api/v1/auth/token/refresh/'
        ]

        # Debug: agregar logging para verificar el path
        print(f"Request path: '{request.path}'")
        print(f"Excluded paths: {auth_excluded_paths}")
        print(f"Path in excluded: {request.path in auth_excluded_paths}")

        if request.path.startswith('/api/') and request.path not in auth_excluded_paths:
            auth = JWTAuthentication()
            try:
                validated_token = auth.get_validated_token(self.get_token_from_request(request))
                user = auth.get_user(validated_token)
                request.user = user
                request.tenant_id = getattr(user, 'tenant_id', None)
            except (InvalidToken, AttributeError):
                # No bloquear, solo continuar sin usuario autenticado
                pass

        response = self.get_response(request)
        return response

    def get_token_from_request(self, request):
        header = request.META.get('HTTP_AUTHORIZATION')
        if header and header.startswith('Bearer '):
            return header.split(' ')[1].encode('utf-8')
        return None
