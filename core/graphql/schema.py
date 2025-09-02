import strawberry
from apps.campaigns.graphql.queries import CampaignQueries
from apps.campaigns.graphql.mutations import CampaignMutations
from apps.authentication.graphql.queries import AuthQueries

@strawberry.type
class Query(CampaignQueries, AuthQueries):
    pass

@strawberry.type
class Mutation(CampaignMutations):
    pass

schema = strawberry.Schema(query=Query, mutation=Mutation)