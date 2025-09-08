from django.db import connection

class AnalyticsRepository:
    @staticmethod
    def cohort_analysis(tenant_id):
        sql = """
        WITH user_first_impression AS (
            SELECT user_id, 
                   DATE(MIN(timestamp)) as cohort_month,
                   MIN(timestamp) as first_impression
            FROM campaigns_impression 
            WHERE tenant_id = %s
            GROUP BY user_id
        ),
        user_activities AS (
            SELECT 
                ci.user_id,
                ufi.cohort_month,
                DATEDIFF(DATE(ci.timestamp), ufi.cohort_month) as period_days,
                COUNT(*) as impressions
            FROM campaigns_impression ci
            JOIN user_first_impression ufi ON ci.user_id = ufi.user_id
            WHERE ci.tenant_id = %s
            GROUP BY ci.user_id, ufi.cohort_month, DATE(ci.timestamp)
        )
        SELECT 
            cohort_month,
            period_days,
            COUNT(DISTINCT user_id) as users,
            SUM(impressions) as total_impressions,
            ROUND(COUNT(DISTINCT user_id) * 100.0 / 
                  FIRST_VALUE(COUNT(DISTINCT user_id)) OVER (
                      PARTITION BY cohort_month ORDER BY period_days
                  ), 2) as retention_rate
        FROM user_activities 
        WHERE period_days <= 30
        GROUP BY cohort_month, period_days
        ORDER BY cohort_month, period_days
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [tenant_id, tenant_id])
            return cursor.fetchall()
    
    @staticmethod
    def campaign_performance_window(tenant_id):
        sql = """
        SELECT 
            ca.id as campaign_id,
            ca.name as campaign_name,
            DATE(ci.timestamp) as date,
            COUNT(*) as impressions,
            SUM(ci.cost) as total_cost,
            AVG(ci.cost) as avg_cost,
            COUNT(DISTINCT ci.user_id) as unique_users,
            ROW_NUMBER() OVER (
                PARTITION BY ca.id ORDER BY COUNT(*) DESC
            ) as daily_rank,
            LAG(COUNT(*)) OVER (
                PARTITION BY ca.id ORDER BY DATE(ci.timestamp)
            ) as prev_day_impressions,
            ROUND(
                (COUNT(*) - LAG(COUNT(*)) OVER (
                    PARTITION BY ca.id ORDER BY DATE(ci.timestamp)
                )) * 100.0 / NULLIF(LAG(COUNT(*)) OVER (
                    PARTITION BY ca.id ORDER BY DATE(ci.timestamp)
                ), 0), 2
            ) as growth_rate
        FROM campaigns_campaign ca
        JOIN campaigns_ad ad ON ad.campaign_id = ca.id
        JOIN campaigns_impression ci ON ci.ad_id = ad.id
        WHERE ca.tenant_id = %s
        GROUP BY ca.id, ca.name, DATE(ci.timestamp)
        HAVING COUNT(*) > 0
        ORDER BY ca.id, date DESC
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [tenant_id])
            return cursor.fetchall()

    @staticmethod
    def top_performing_campaigns(tenant_id, limit=10):
        sql = """
        WITH campaign_metrics AS (
            SELECT 
                ca.id,
                ca.name,
                COUNT(ci.id) as total_impressions,
                SUM(ci.cost) as total_spend,
                COUNT(DISTINCT ci.user_id) as unique_users,
                ROUND(SUM(ci.cost) / COUNT(ci.id), 4) as avg_cpm
            FROM campaigns_campaign ca
            JOIN campaigns_ad ad ON ad.campaign_id = ca.id
            JOIN campaigns_impression ci ON ci.ad_id = ad.id
            WHERE ca.tenant_id = %s
            GROUP BY ca.id, ca.name
        )
        SELECT *,
               RANK() OVER (ORDER BY total_impressions DESC) as impression_rank,
               RANK() OVER (ORDER BY avg_cpm ASC) as efficiency_rank
        FROM campaign_metrics
        ORDER BY total_impressions DESC
        LIMIT %s
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [tenant_id, limit])
            return cursor.fetchall()