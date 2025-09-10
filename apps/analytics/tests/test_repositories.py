from django.test import TestCase
from django.test import TransactionTestCase
from apps.analytics.repository import AnalyticsRepository
from apps.campaigns.models import Campaign, Ad, Impression
from apps.authentication.models import User
import time

class AnalyticsRepositoryTest(TransactionTestCase):
    def setUp(self):
        # Crear datos de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass',
            tenant_id=1
        )
        
    def test_cohort_analysis_performance(self):
        # Test que query termine en <500ms
        start = time.time()
        result = AnalyticsRepository.advanced_cohort_analysis(1, 30)
        duration = time.time() - start
        self.assertLess(duration, 0.5)  # <500ms
        self.assertIsInstance(result, list)
        
    def test_real_time_metrics(self):
        start = time.time()
        result = AnalyticsRepository.get_real_time_metrics(1)
        duration = time.time() - start
        self.assertLess(duration, 0.1)  # <100ms for real-time
        self.assertIn('impressions_last_hour', result)
