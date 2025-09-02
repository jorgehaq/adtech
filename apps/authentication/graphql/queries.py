import strawberry
from typing import List
from apps.authentication.models import User
from .types import UserType

@strawberry.type
class AuthQueries:
    
    @strawberry.field
    def users(self) -> List[UserType]:
        return User.objects.all()
    
    @strawberry.field
    def user(self, id: int) -> UserType:
        return User.objects.get(id=id)