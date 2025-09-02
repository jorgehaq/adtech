import strawberry_django
from strawberry import auto
from apps.campaigns.models import Campaign, Ad, Impression

@strawberry_django.type(Campaign)
class CampaignType:
    id: auto
    tenant_id: auto
    name: auto
    budget: auto
    status: auto
    start_date: auto
    end_date: auto

@strawberry_django.type(Ad)
class AdType:
    id: auto
    tenant_id: auto
    campaign: CampaignType
    creative_url: auto
    target_audience: auto

@strawberry_django.type(Impression)
class ImpressionType:
    id: auto
    tenant_id: auto
    ad: AdType
    user_id: auto
    timestamp: auto
    cost: auto