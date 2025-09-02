from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.authentication.models import UserPermission

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a tenant user with specific permissions'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--password', type=str, required=True)
        parser.add_argument('--tenant_id', type=int, required=True)
        parser.add_argument('--role', type=str, default='user')
        parser.add_argument('--username', type=str, required=True)

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        tenant_id = options['tenant_id']
        role = options['role']
        username = options['username']

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'User with email {email} already exists')
            )
            return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            tenant_id=tenant_id,
            role=role
        )

        # Create default permissions for admin users
        if role in ['admin', 'super_admin']:
            default_permissions = [
                {'resource': 'campaigns', 'action': 'read'},
                {'resource': 'campaigns', 'action': 'write'},
                {'resource': 'campaigns', 'action': 'delete'},
                {'resource': 'ads', 'action': 'read'},
                {'resource': 'ads', 'action': 'write'},
                {'resource': 'ads', 'action': 'delete'},
                {'resource': 'analytics', 'action': 'read'},
            ]

            for perm in default_permissions:
                UserPermission.objects.create(
                    user=user,
                    resource=perm['resource'],
                    action=perm['action'],
                    tenant_id=tenant_id
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created user {email} for tenant {tenant_id}'
            )
        )