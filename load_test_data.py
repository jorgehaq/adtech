
#!/usr/bin/env python
"""
Script para cargar datos de prueba para testing de Celery y analytics
"""
import os
import sys
import django
import random
from datetime import datetime, timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local')
django.setup()

from apps.campaigns.models import Campaign, Ad, Impression
from apps.authentication.models import User

def create_test_data():
    print("🚀 Creating test data for Celery analytics...")
    
    # 1. Crear usuario de prueba si no existe
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@adtech.com',
            'tenant_id': 1,
            'role': 'user'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.email}")
    
    # 2. Crear campaña de prueba si no existe
    campaign, created = Campaign.objects.get_or_create(
        tenant_id=1,
        name='Test Campaign for Analytics',
        defaults={
            'budget': 10000.00,
            'status': 'active',
            'start_date': '2025-01-01',
            'end_date': '2025-12-31'
        }
    )
    if created:
        print(f"✅ Created test campaign: {campaign.name}")
    
    # 3. Crear ad de prueba si no existe
    ad, created = Ad.objects.get_or_create(
        tenant_id=1,
        campaign=campaign,
        defaults={
            'creative_url': 'https://example.com/banner.jpg',
            'target_audience': 'Test audience for analytics'
        }
    )
    if created:
        print(f"✅ Created test ad for campaign: {campaign.name}")
    
    # 4. Crear 1000 impresiones para testing de analytics
    print("📊 Creating 1000 impressions for analytics testing...")
    
    impressions_to_create = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(1000):
        # Distribuir impresiones en los últimos 30 días
        timestamp = base_time + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        impression = Impression(
            tenant_id=1,
            ad=ad,
            user_id=random.randint(1, 100),
            cost=round(random.uniform(0.1, 2.0), 4),
            timestamp=timestamp
        )
        impressions_to_create.append(impression)
        
        # Batch create cada 100 registros
        if len(impressions_to_create) == 100:
            Impression.objects.bulk_create(impressions_to_create)
            impressions_to_create = []
            print(f"✅ Created {i+1} impressions...")
    
    # Crear los restantes
    if impressions_to_create:
        Impression.objects.bulk_create(impressions_to_create)
    
    # 5. Mostrar estadísticas
    total_impressions = Impression.objects.filter(tenant_id=1).count()
    total_cost = sum(imp.cost for imp in Impression.objects.filter(tenant_id=1))
    
    print(f"\n📈 Test data created successfully!")
    print(f"   - Total impressions: {total_impressions}")
    print(f"   - Total cost: ${total_cost:.2f}")
    print(f"   - Campaign: {campaign.name}")
    print(f"   - Ad ID: {ad.id}")
    print(f"   - Tenant ID: 1")
    
    print(f"\n🧪 Ready for Celery analytics testing:")
    print(f"   - Cohort analysis with {total_impressions} impressions")
    print(f"   - Performance queries with window functions")
    print(f"   - Background aggregation tasks")

if __name__ == '__main__':
    create_test_data()
