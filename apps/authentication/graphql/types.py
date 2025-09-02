import strawberry
import strawberry.django
from strawberry import auto
from apps.authentication.models import User

@strawberry.django.type(User)
class UserType:
    id: auto
    username: auto
    email: auto
    tenant_id: auto
    role: auto
    date_joined: auto