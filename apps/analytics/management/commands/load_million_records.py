from django.core.management.base import BaseCommand
from django.db import transaction
from apps.campaigns.models import Campaign, Ad, Impression
from apps.authentication.models import User
from apps.advertisers.models import Advertiser
from apps.creatives.models import Creative
from apps.audiences.models import AudienceSegment
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Load million records for performance testing'

    def add_arguments(self, parser):
        parser.add_argument('--records', type=int, default=1000000, help='Number of impressions to create')
        parser.add_argument('--tenant_id', type=int, default=1, help='Tenant ID for records')
        parser.add_argument('--batch_size', type=int, default=10000, help='Batch size for bulk creation')
        parser.add_argument('--days_back', type=int, default=90, help='Days back for data distribution')

    def handle(self, *args, **options):
        records = options['records']
        tenant_id = options['tenant_id']
        batch_size = options['batch_size']
        days_back = options['days_back']

        self.stdout.write(
            self.style.SUCCESS(f'Starting to load {records:,} records for tenant {tenant_id}')
        )

        # 1. Ensure base data exists
        advertiser = self.ensure_advertiser(tenant_id)
        creative = self.ensure_creative(tenant_id)
        audience = self.ensure_audience(tenant_id)
        campaigns, ads = self.ensure_campaigns_and_ads(tenant_id, advertiser, creative, audience)

        # 2. Create impressions in batches
        total_created = self.create_impressions_batch(
            ads, records, batch_size, days_back, tenant_id
        )

        # 3. Show final stats
        self.show_stats(tenant_id, total_created)

    def ensure_advertiser(self, tenant_id):
        advertiser, created = Advertiser.objects.get_or_create(
            tenant_id=tenant_id,
            name='Performance Test Advertiser',
            defaults={
                'email': 'perf@adtech.com',
                'status': 'active'
            }
        )
        if created:
            self.stdout.write(f'✅ Created advertiser: {advertiser.name}')
        return advertiser

    def ensure_creative(self, tenant_id):
        creative, created = Creative.objects.get_or_create(
            tenant_id=tenant_id,
            name='Performance Test Creative',
            defaults={
                'asset_url': 'https://example.com/perf-banner.jpg',
                'creative_type': 'banner',
                'status': 'active'
            }
        )
        if created:
            self.stdout.write(f'✅ Created creative: {creative.name}')
        return creative

    def ensure_audience(self, tenant_id):
        audience, created = AudienceSegment.objects.get_or_create(
            tenant_id=tenant_id,
            name='Performance Test Audience',
            defaults={
                'description': 'Large audience for performance testing',
                'criteria': {'age': '18-65', 'location': 'global'},
                'size': 1000000
            }
        )
        if created:
            self.stdout.write(f'✅ Created audience: {audience.name}')
        return audience

    def ensure_campaigns_and_ads(self, tenant_id, advertiser, creative, audience):
        campaigns = []
        ads = []

        # Create 10 campaigns
        for i in range(10):
            campaign, created = Campaign.objects.get_or_create(
                tenant_id=tenant_id,
                name=f'Performance Campaign {i+1}',
                defaults={
                    'advertiser': advertiser,
                    'budget': random.uniform(5000, 50000),
                    'status': 'active',
                    'start_date': '2024-01-01',
                    'end_date': '2025-12-31'
                }
            )
            campaigns.append(campaign)

            if created:
                # Create 3-5 ads per campaign
                for j in range(random.randint(3, 5)):
                    ad = Ad.objects.create(
                        tenant_id=tenant_id,
                        campaign=campaign,
                        creative=creative,
                        audience=audience,
                        creative_url=f'https://example.com/ad-{i}-{j}.jpg',
                        target_audience=f'Segment {i}-{j}'
                    )
                    ads.append(ad)

        # Get all ads for this tenant
        all_ads = list(Ad.objects.filter(tenant_id=tenant_id))
        
        self.stdout.write(f'✅ Ensured {len(campaigns)} campaigns and {len(all_ads)} ads')
        return campaigns, all_ads

    def create_impressions_batch(self, ads, total_records, batch_size, days_back, tenant_id):
        self.stdout.write(f'🚀 Creating {total_records:,} impressions in batches of {batch_size:,}')
        
        total_batches = total_records // batch_size
        base_time = datetime.now() - timedelta(days=days_back)
        total_created = 0

        for batch_num in range(total_batches):
            impressions_batch = []

            for i in range(batch_size):
                # Distribute impressions over time period
                timestamp = base_time + timedelta(
                    days=random.randint(0, days_back),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )

                impression = Impression(
                    tenant_id=tenant_id,
                    ad=random.choice(ads),
                    user_id=random.randint(1000, 999999),
                    cost=round(random.uniform(0.05, 3.0), 4),
                    timestamp=timestamp
                )
                impressions_batch.append(impression)

            # Bulk create with transaction
            try:
                with transaction.atomic():
                    Impression.objects.bulk_create(impressions_batch, batch_size=1000)
                
                total_created += len(impressions_batch)
                progress = (batch_num + 1) / total_batches * 100
                
                self.stdout.write(f'Progress: {progress:.1f}% ({total_created:,}/{total_records:,})')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error in batch {batch_num}: {e}')
                )
                continue

        return total_created

    def show_stats(self, tenant_id, total_created):
        total_impressions = Impression.objects.filter(tenant_id=tenant_id).count()
        total_campaigns = Campaign.objects.filter(tenant_id=tenant_id).count()
        total_ads = Ad.objects.filter(tenant_id=tenant_id).count()

        self.stdout.write(
            self.style.SUCCESS(f'\n📊 FINAL STATISTICS:')
        )
        self.stdout.write(f'   Total Impressions: {total_impressions:,}')
        self.stdout.write(f'   Total Campaigns: {total_campaigns}')
        self.stdout.write(f'   Total Ads: {total_ads}')
        self.stdout.write(f'   Records Created: {total_created:,}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🔥 Ready for performance testing with {total_impressions:,} records')
        )