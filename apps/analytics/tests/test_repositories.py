# apps/analytics/tests/test_repositories.py
from django.test import TestCase
from apps.analytics.repositories import AnalyticsRepository

class AnalyticsRepositoryTest(TestCase):
    def test_cohort_analysis_performance(self):
        # Test que query termine en <500ms
        import time
        start = time.time()
        result = AnalyticsRepository.advanced_cohort_analysis(1, 30)
        duration = time.time() - start
        self.assertLess(duration, 0.5)  # <500ms