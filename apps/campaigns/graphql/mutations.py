import strawberry
from typing import Optional
from apps.campaigns.models import Campaign, Ad
from .types import CampaignType, AdType

@strawberry.input
class CampaignInput:
    tenant_id: int
    name: str
    budget: str
    status: str
    start_date: str
    end_date: str

@strawberry.input
class AdInput:
    tenant_id: int
    campaign_id: int
    creative_url: str
    target_audience: str

@strawberry.type
class CampaignMutations:
    
    @strawberry.mutation
    def create_campaign(self, info, input: CampaignInput) -> CampaignType:
        tenant_id = info.context.request.user.tenant_id
        campaign = Campaign.objects.create(
            tenant_id=tenant_id,  # Forzar tenant
            name=input.name,
            budget=input.budget,
            status=input.status,
            start_date=input.start_date,
            end_date=input.end_date
        )
        return campaign
    
    @strawberry.mutation
    def create_ad(self, input: AdInput) -> AdType:
        ad = Ad.objects.create(
            tenant_id=input.tenant_id,
            campaign_id=input.campaign_id,
            creative_url=input.creative_url,
            target_audience=input.target_audience
        )
        return ad