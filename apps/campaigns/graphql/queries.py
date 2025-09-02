import strawberry
from typing import List
from apps.campaigns.models import Campaign, Ad
from .types import CampaignType, AdType

@strawberry.type
class CampaignQueries:
    
    @strawberry.field
    def campaigns(self) -> List[CampaignType]:
        return Campaign.objects.all()
    
    @strawberry.field
    def campaign(self, id: int) -> CampaignType:
        return Campaign.objects.get(id=id)
    
    @strawberry.field
    def ads(self) -> List[AdType]:
        return Ad.objects.select_related('campaign').all()
    
    @strawberry.field
    def ad(self, id: int) -> AdType:
        return Ad.objects.select_related('campaign').get(id=id)