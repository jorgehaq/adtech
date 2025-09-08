# apps/analytics/management/commands/load_million_records.py
from django.core.management.base import BaseCommand
from apps.campaigns.models import Campaign, Ad, Impression
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Crear 1M impressions en batches de 10k
        for batch in range(100):
            impressions = []
            for i in range(10000):
                # Lógica de creación masiva
            Impression.objects.bulk_create(impressions)
            self.stdout.write(f"Batch {batch+1}/100 completed")