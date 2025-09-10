# apps/analytics/bigquery.py
from google.cloud import bigquery

class BigQueryAnalytics:
    def __init__(self):
        self.client = bigquery.Client()
        self.dataset_id = "adtech_analytics"
    
    def sync_impressions(self, tenant_id):
        query = """
        INSERT INTO `{}.impressions` (tenant_id, campaign_id, cost, timestamp)
        SELECT %s, campaign_id, cost, timestamp 
        FROM campaigns_impression 
        WHERE tenant_id = %s AND sync_status = 'pending'
        """.format(self.dataset_id)
        
        job = self.client.query(query, [tenant_id, tenant_id])
        return job.result()
    
    def cohort_analysis_bigquery(self, tenant_id):
        query = """
        WITH user_cohorts AS (
          SELECT user_id, DATE_TRUNC(MIN(timestamp), MONTH) as cohort_month
          FROM `{}.impressions`
          WHERE tenant_id = @tenant_id
          GROUP BY user_id
        )
        SELECT cohort_month, COUNT(*) as users
        FROM user_cohorts
        GROUP BY cohort_month
        ORDER BY cohort_month
        """.format(self.dataset_id)
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("tenant_id", "INT64", tenant_id)
            ]
        )
        return self.client.query(query, job_config=job_config).result()