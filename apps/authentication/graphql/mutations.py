# apps/authentication/graphql/mutations.py
import strawberry

@strawberry.type
class AuthMutations:
    @strawberry.mutation
    def placeholder(self) -> str:
        return "auth mutations placeholder"