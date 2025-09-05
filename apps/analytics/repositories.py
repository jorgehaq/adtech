from django.db import connection

class AnalyticsRepository:
    @staticmethod
    def cohort_analysis(tenant_id):
        sql = """
        WITH cohort_data AS (
            SELECT user_id, 
                   DATE(MIN(timestamp)) as cohort_month,
                   DATEDIFF(DAY, MIN(timestamp), timestamp) as period_days
            FROM campaigns_impression 
            WHERE tenant_id = %s
            GROUP BY user_id, DATE(timestamp)
        )
        SELECT cohort_month, period_days, COUNT(DISTINCT user_id) as users
        FROM cohort_data 
        GROUP BY cohort_month, period_days
        ORDER BY cohort_month, period_days
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [tenant_id])
            return cursor.fetchall()
    
    @staticmethod
    def campaign_performance_window(tenant_id):
        sql = """
        SELECT campaign_id,
               DATE(timestamp) as date,
               COUNT(*) as impressions,
               SUM(cost) as total_cost,
               ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY COUNT(*) DESC) as rank,
               LAG(COUNT(*)) OVER (PARTITION BY campaign_id ORDER BY DATE(timestamp)) as prev_impressions
        FROM campaigns_impression 
        WHERE tenant_id = %s
        GROUP BY campaign_id, DATE(timestamp)
        ORDER BY campaign_id, date
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [tenant_id])
            return cursor.fetchall()
        

    @staticmethod
    def campaign_performance_hourly(tenant_id):
        sql = """
        SELECT campaign_id,
               DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00') as hour,
               COUNT(*) as impressions,
               SUM(cost) as spend,
               AVG(cost) as avg_cost,
               ROW_NUMBER() OVER (PARTITION BY campaign_id ORDER BY COUNT(*) DESC) as rank
        FROM campaigns_impression 
        WHERE tenant_id = %s
        GROUP BY campaign_id, DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00')
        """
