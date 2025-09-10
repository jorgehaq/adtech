from django.db import connection
from typing import List, Dict, Any
from .repositories.connection import optimized_analytics_cursor
from .repositories.performance import monitor_query_performance

class AnalyticsRepository:
    @staticmethod
    @monitor_query_performance
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
        with optimized_analytics_cursor() as cursor:
            cursor.execute(sql, [tenant_id, tenant_id])
            return cursor.fetchall()
    
    @staticmethod
    @monitor_query_performance
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
        with optimized_analytics_cursor() as cursor:
            cursor.execute(sql, [tenant_id])
            return cursor.fetchall()

    @staticmethod
    @monitor_query_performance
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
        with optimized_analytics_cursor() as cursor:
            cursor.execute(sql, [tenant_id, limit])
            return cursor.fetchall()
        
    @staticmethod
    @monitor_query_performance
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
        
        with optimized_analytics_cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
        
    
    @staticmethod
    @monitor_query_performance
    def get_real_time_metrics(tenant_id: int, campaign_id: int = None) -> Dict[str, Any]:
        """Sub-100ms real-time metrics query"""
        sql = """
        SELECT 
            COUNT(*) as impressions_last_hour,
            COUNT(DISTINCT ci.user_id) as unique_users,
            COALESCE(SUM(ci.cost), 0) as spend_last_hour,
            COALESCE(AVG(ci.cost), 0) as avg_cpm,
            COUNT(*) / NULLIF(COUNT(DISTINCT ci.user_id), 0) as frequency
        FROM campaigns_impression ci
        JOIN campaigns_ad ad ON ci.ad_id = ad.id
        WHERE ci.tenant_id = %s 
        AND ci.timestamp >= NOW() - INTERVAL 1 HOUR
        """ + (" AND ad.campaign_id = %s" if campaign_id else "")
        
        params = [tenant_id]
        if campaign_id:
            params.append(campaign_id)
            
        with optimized_analytics_cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return {
                'impressions_last_hour': row[0] or 0,
                'unique_users': row[1] or 0,
                'spend_last_hour': float(row[2] or 0),
                'avg_cpm': float(row[3] or 0),
                'frequency': float(row[4] or 0)
            }

    @staticmethod
    @monitor_query_performance
    def advanced_cohort_analysis(tenant_id: int, days_back: int = 30) -> List[Dict]:
        """Production-level cohort analysis with window functions"""
        sql = """
        WITH user_first_impression AS (
            SELECT 
                user_id,
                DATE(MIN(timestamp)) as cohort_month,
                MIN(timestamp) as first_impression_time
            FROM campaigns_impression 
            WHERE tenant_id = %s
            AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY user_id
        ),
        user_activities AS (
            SELECT 
                ufi.cohort_month,
                ufi.user_id,
                DATEDIFF(DATE(ci.timestamp), ufi.cohort_month) as period_days,
                COUNT(*) as activity_count,
                SUM(ci.cost) as total_spend
            FROM user_first_impression ufi
            JOIN campaigns_impression ci ON ufi.user_id = ci.user_id
            WHERE ci.tenant_id = %s
            AND DATEDIFF(DATE(ci.timestamp), ufi.cohort_month) <= 30
            GROUP BY ufi.cohort_month, ufi.user_id, DATEDIFF(DATE(ci.timestamp), ufi.cohort_month)
        ),
        cohort_metrics AS (
            SELECT 
                cohort_month,
                period_days,
                COUNT(DISTINCT user_id) as active_users,
                SUM(activity_count) as total_impressions,
                SUM(total_spend) as cohort_spend,
                FIRST_VALUE(COUNT(DISTINCT user_id)) OVER (
                    PARTITION BY cohort_month ORDER BY period_days
                ) as cohort_size
            FROM user_activities
            GROUP BY cohort_month, period_days
        )
        SELECT 
            cohort_month,
            period_days,
            active_users,
            total_impressions,
            cohort_spend,
            cohort_size,
            ROUND(active_users * 100.0 / cohort_size, 2) as retention_rate,
            ROUND(cohort_spend / active_users, 4) as revenue_per_user
        FROM cohort_metrics
        ORDER BY cohort_month, period_days
        """
        
        with optimized_analytics_cursor() as cursor:
            cursor.execute(sql, [tenant_id, days_back, tenant_id])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def campaign_performance_ranking(tenant_id: int, limit: int = 20) -> List[Dict]:
        """Advanced campaign ranking with multiple metrics"""
        sql = """
        WITH campaign_metrics AS (
            SELECT 
                ca.id as campaign_id,
                ca.name as campaign_name,
                ca.budget,
                COUNT(ci.id) as total_impressions,
                COUNT(DISTINCT ci.user_id) as unique_users,
                SUM(ci.cost) as total_spend,
                AVG(ci.cost) as avg_cpm,
                COUNT(ci.id) / NULLIF(COUNT(DISTINCT ci.user_id), 0) as frequency,
                DATEDIFF(NOW(), ca.start_date) as days_running
            FROM campaigns_campaign ca
            LEFT JOIN campaigns_ad ad ON ad.campaign_id = ca.id
            LEFT JOIN campaigns_impression ci ON ci.ad_id = ad.id AND ci.tenant_id = %s
            WHERE ca.tenant_id = %s AND ca.status = 'active'
            GROUP BY ca.id, ca.name, ca.budget, ca.start_date
            HAVING total_impressions > 0
        ),
        performance_scores AS (
            SELECT *,
                ROUND(total_spend / NULLIF(budget, 0) * 100, 2) as budget_utilization,
                ROUND(total_impressions / NULLIF(days_running, 0), 0) as daily_impression_rate,
                ROW_NUMBER() OVER (ORDER BY total_impressions DESC) as impression_rank,
                ROW_NUMBER() OVER (ORDER BY avg_cpm ASC) as efficiency_rank,
                ROW_NUMBER() OVER (ORDER BY unique_users DESC) as reach_rank
            FROM campaign_metrics
        )
        SELECT *,
            ROUND((impression_rank + efficiency_rank + reach_rank) / 3.0, 1) as overall_score
        FROM performance_scores
        ORDER BY overall_score ASC
        LIMIT %s
        """
        
        with optimized_analytics_cursor() as cursor:
            cursor.execute(sql, [tenant_id, tenant_id, limit])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def hourly_performance_trend(tenant_id: int, campaign_id: int, hours_back: int = 24) -> List[Dict]:
        """Hourly performance analysis for real-time monitoring"""
        sql = """
        SELECT 
            DATE_FORMAT(ci.timestamp, '%%Y-%%m-%%d %%H:00:00') as hour_bucket,
            COUNT(*) as impressions,
            COUNT(DISTINCT ci.user_id) as unique_users,
            SUM(ci.cost) as spend,
            AVG(ci.cost) as avg_cost,
            LAG(COUNT(*)) OVER (ORDER BY DATE_FORMAT(ci.timestamp, '%%Y-%%m-%%d %%H:00:00')) as prev_hour_impressions,
            CASE 
                WHEN LAG(COUNT(*)) OVER (ORDER BY DATE_FORMAT(ci.timestamp, '%%Y-%%m-%%d %%H:00:00')) IS NULL THEN 0
                ELSE ROUND((COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY DATE_FORMAT(ci.timestamp, '%%Y-%%m-%%d %%H:00:00'))) * 100.0 / 
                     NULLIF(LAG(COUNT(*)) OVER (ORDER BY DATE_FORMAT(ci.timestamp, '%%Y-%%m-%%d %%H:00:00')), 0), 2)
            END as growth_rate
        FROM campaigns_impression ci
        JOIN campaigns_ad ad ON ci.ad_id = ad.id
        WHERE ci.tenant_id = %s 
        AND ad.campaign_id = %s
        AND ci.timestamp >= NOW() - INTERVAL %s HOUR
        GROUP BY DATE_FORMAT(ci.timestamp, '%%Y-%%m-%%d %%H:00:00')
        ORDER BY hour_bucket DESC
        """
        
        with optimized_analytics_cursor() as cursor:
            cursor.execute(sql, [tenant_id, campaign_id, hours_back])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def get_query_performance_stats() -> Dict[str, Any]:
        """Monitor query performance for optimization"""
        sql = """
        SELECT 
            COUNT(*) as total_queries,
            AVG(QUERY_TIME) as avg_query_time,
            MAX(QUERY_TIME) as max_query_time,
            SUM(CASE WHEN QUERY_TIME > 1 THEN 1 ELSE 0 END) as slow_queries
        FROM information_schema.PROCESSLIST 
        WHERE COMMAND = 'Query' AND DB = DATABASE()
        """
        
        with optimized_analytics_cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()
            return {
                'total_queries': row[0] or 0,
                'avg_query_time': float(row[1] or 0),
                'max_query_time': float(row[2] or 0),
                'slow_queries': row[3] or 0
            }
