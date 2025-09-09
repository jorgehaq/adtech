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
        
    @staticmethod
    def attribution_analysis(tenant_id, campaign_id=None):
        """Multi-level CTE for attribution modeling"""
        sql = """
        WITH user_journeys AS (
            SELECT 
                ci.user_id,
                ci.timestamp as impression_time,
                cc.timestamp as click_time,
                cv.timestamp as conversion_time,
                cv.conversion_value,
                ad.campaign_id,
                ROW_NUMBER() OVER (
                    PARTITION BY ci.user_id 
                    ORDER BY ci.timestamp
                ) as journey_step
            FROM campaigns_impression ci
            LEFT JOIN campaigns_ad ad ON ci.ad_id = ad.id
            LEFT JOIN events_clickevent cc ON cc.impression_id = ci.id
            LEFT JOIN events_conversionevent cv ON cv.click_id = cc.id
            WHERE ci.tenant_id = %s
        ),
        touch_points AS (
            SELECT 
                user_id,
                campaign_id,
                COUNT(*) as impressions,
                COUNT(click_time) as clicks,
                COUNT(conversion_time) as conversions,
                SUM(conversion_value) as total_value,
                MIN(impression_time) as first_touch,
                MAX(impression_time) as last_touch,
                DATEDIFF(MAX(impression_time), MIN(impression_time)) as journey_length
            FROM user_journeys
            GROUP BY user_id, campaign_id
        ),
        attribution_weights AS (
            SELECT 
                tp.*,
                CASE 
                    WHEN journey_length = 0 THEN 1.0
                    WHEN journey_step = 1 THEN 0.4  -- First touch
                    WHEN conversion_time IS NOT NULL THEN 0.4  -- Last touch
                    ELSE 0.2  -- Middle touches
                END as attribution_weight
            FROM touch_points tp
            JOIN user_journeys uj ON tp.user_id = uj.user_id AND tp.campaign_id = uj.campaign_id
        )
        SELECT 
            campaign_id,
            COUNT(DISTINCT user_id) as attributed_users,
            SUM(total_value * attribution_weight) as attributed_revenue,
            AVG(journey_length) as avg_journey_days,
            SUM(impressions) as total_impressions,
            SUM(clicks) as total_clicks,
            SUM(conversions) as total_conversions
        FROM attribution_weights
        GROUP BY campaign_id
        ORDER BY attributed_revenue DESC
        """
        
        params = [tenant_id]
        if campaign_id:
            sql += " HAVING campaign_id = %s"
            params.append(campaign_id)
        
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()