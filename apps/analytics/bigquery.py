from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from django.conf import settings
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BigQueryAnalytics:
    def __init__(self):
        self.dataset_id = "adtech_analytics"
        self.project_id = settings.GCP_PROJECT_ID if hasattr(settings, 'GCP_PROJECT_ID') else 'adtech-project'
        self.mock_mode = getattr(settings, 'DEBUG', False)

        if self.mock_mode:
            self.client = None
        else:
            self.client = bigquery.Client()

    
    def ensure_dataset_exists(self):
        """Create dataset if it doesn't exist"""
        dataset_ref = self.client.dataset(self.dataset_id)
        try:
            self.client.get_dataset(dataset_ref)
        except NotFound:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            self.client.create_dataset(dataset)
            logger.info(f"Created dataset {self.dataset_id}")
    
    def ensure_tables_exist(self):
        """Create required tables"""
        self.ensure_dataset_exists()
        
        # Impressions table
        impressions_schema = [
            bigquery.SchemaField("tenant_id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("campaign_id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("ad_id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("cost", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("country", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("device_type", "STRING", mode="NULLABLE"),
        ]
        
        self._create_table_if_not_exists("impressions", impressions_schema)
        
        # Daily metrics table
        metrics_schema = [
            bigquery.SchemaField("tenant_id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("campaign_id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("impressions", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("clicks", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("conversions", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("spend", "FLOAT", mode="REQUIRED"),
        ]
        
        self._create_table_if_not_exists("daily_metrics", metrics_schema)
    
    def _create_table_if_not_exists(self, table_name: str, schema: List[bigquery.SchemaField]):
        """Helper to create table if it doesn't exist"""
        table_ref = self.client.dataset(self.dataset_id).table(table_name)
        try:
            self.client.get_table(table_ref)
        except NotFound:
            table = bigquery.Table(table_ref, schema=schema)
            if table_name == "impressions":
                table.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field="timestamp"
                )
            self.client.create_table(table)
            logger.info(f"Created table {table_name}")






    def sync_impressions(self, tenant_id: int, batch_size: int = 10000) -> Dict[str, Any]:
        """Sync impressions from MySQL to BigQuery"""
        if self.mock_mode:
            return {
                "synced_rows": 1500, 
                "status": "mock_success",
                "last_timestamp": "2025-01-15T10:30:00"
            }

        self.ensure_tables_exist()

        from django.db import connection
        
        # Get latest synced timestamp
        last_sync = self._get_last_sync_timestamp(tenant_id, "impressions")
        
        # Query new impressions from MySQL
        sql = """
        SELECT 
            ci.tenant_id,
            ad.campaign_id,
            ci.ad_id,
            ci.user_id,
            ci.cost,
            ci.timestamp,
            'US' as country,
            'desktop' as device_type
        FROM campaigns_impression ci
        JOIN campaigns_ad ad ON ci.ad_id = ad.id
        WHERE ci.tenant_id = %s 
        AND ci.timestamp > %s
        ORDER BY ci.timestamp
        LIMIT %s
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql, [tenant_id, last_sync, batch_size])
            rows = cursor.fetchall()
        
        if not rows:
            return {"synced_rows": 0, "status": "no_new_data"}
        
        # Insert into BigQuery
        table_ref = self.client.dataset(self.dataset_id).table("impressions")
        
        # Convert to BigQuery format
        bq_rows = []
        for row in rows:
            bq_rows.append({
                "tenant_id": row[0],
                "campaign_id": row[1], 
                "ad_id": row[2],
                "user_id": row[3],
                "cost": float(row[4]),
                "timestamp": row[5].isoformat(),
                "country": row[6],
                "device_type": row[7]
            })
        
        # Insert rows
        errors = self.client.insert_rows_json(table_ref, bq_rows)
        
        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            return {"synced_rows": 0, "status": "error", "errors": errors}
        
        # Update sync timestamp
        self._update_last_sync_timestamp(tenant_id, "impressions", rows[-1][5])
        
        return {
            "synced_rows": len(rows),
            "status": "success",
            "last_timestamp": rows[-1][5].isoformat()
        }



    def campaign_performance_bigquery(self, tenant_id: int, campaign_id: int = None) -> List[Dict]:
        """Campaign performance analysis in BigQuery"""
        where_clause = "AND campaign_id = @campaign_id" if campaign_id else ""
        
        query = f"""
        SELECT 
            campaign_id,
            DATE(timestamp) as date,
            COUNT(*) as impressions,
            COUNT(DISTINCT user_id) as unique_users,
            SUM(cost) as total_cost,
            AVG(cost) as avg_cost,
            LAG(COUNT(*)) OVER (
                PARTITION BY campaign_id ORDER BY DATE(timestamp)
            ) as prev_day_impressions,
            CASE 
                WHEN LAG(COUNT(*)) OVER (
                    PARTITION BY campaign_id ORDER BY DATE(timestamp)
                ) IS NULL THEN 0
                ELSE ROUND(
                    (COUNT(*) - LAG(COUNT(*)) OVER (
                        PARTITION BY campaign_id ORDER BY DATE(timestamp)
                    )) * 100.0 / LAG(COUNT(*)) OVER (
                        PARTITION BY campaign_id ORDER BY DATE(timestamp)
                    ), 2
                )
            END as growth_rate
        FROM `{self.project_id}.{self.dataset_id}.impressions`
        WHERE tenant_id = @tenant_id
        {where_clause}
        AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY campaign_id, DATE(timestamp)
        ORDER BY campaign_id, date DESC
        """
        
        params = [bigquery.ScalarQueryParameter("tenant_id", "INT64", tenant_id)]
        if campaign_id:
            params.append(bigquery.ScalarQueryParameter("campaign_id", "INT64", campaign_id))
        
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        return [dict(row) for row in results]
    
    def _get_last_sync_timestamp(self, tenant_id: int, table_name: str) -> datetime:
        """Get last sync timestamp from sync log"""
        # Default to 30 days ago if no sync record
        return datetime.now() - timedelta(days=30)
    
    def _update_last_sync_timestamp(self, tenant_id: int, table_name: str, timestamp: datetime):
        """Update last sync timestamp"""
        # In production, store in a sync_log table
        pass
    
    def get_sync_status(self, tenant_id: int) -> Dict[str, Any]:
        """Get BigQuery sync status"""
        if self.mock_mode:
            return {
                "status": "mock_connected",
                "total_rows": 50000,
                "campaigns": 5,
                "latest_timestamp": "2025-01-15T10:30:00",
                "earliest_timestamp": "2025-01-01T00:00:00",
                "tenant_id": tenant_id
            }
        
        # Check row counts
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT campaign_id) as campaigns,
            MAX(timestamp) as latest_timestamp,
            MIN(timestamp) as earliest_timestamp
        FROM `{self.project_id}.{self.dataset_id}.impressions`
        WHERE tenant_id = @tenant_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("tenant_id", "INT64", tenant_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results:
                row = results[0]
                return {
                    "status": "connected",
                    "total_rows": row[0],
                    "campaigns": row[1], 
                    "latest_timestamp": row[2].isoformat() if row[2] else None,
                    "earliest_timestamp": row[3].isoformat() if row[3] else None,
                    "tenant_id": tenant_id
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "tenant_id": tenant_id
            }
        
        return {"status": "no_data", "tenant_id": tenant_id}



    
    def cohort_analysis_bigquery(self, tenant_id: int, days_back: int = 30) -> List[Dict]:
        """Advanced cohort analysis using BigQuery"""
        if self.mock_mode:
            return [
                {
                    "cohort_month": "2025-01-01",
                    "period_days": 0,
                    "active_users": 1000,
                    "total_impressions": 5000,
                    "cohort_spend": 2500.0,
                    "cohort_size": 1000,
                    "retention_rate": 100.0,
                    "revenue_per_user": 2.5
                }
            ]
        
        query = f"""
        WITH user_first_impression AS (
            SELECT 
                user_id,
                DATE(MIN(timestamp)) as cohort_month,
                MIN(timestamp) as first_impression_time
            FROM `{self.project_id}.{self.dataset_id}.impressions`
            WHERE tenant_id = @tenant_id
            AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days_back DAY)
            GROUP BY user_id
        ),
        user_activities AS (
            SELECT 
                ufi.cohort_month,
                ufi.user_id,
                DATE_DIFF(DATE(i.timestamp), ufi.cohort_month, DAY) as period_days,
                COUNT(*) as activity_count,
                SUM(i.cost) as total_spend
            FROM user_first_impression ufi
            JOIN `{self.project_id}.{self.dataset_id}.impressions` i 
                ON ufi.user_id = i.user_id
            WHERE i.tenant_id = @tenant_id
            AND DATE_DIFF(DATE(i.timestamp), ufi.cohort_month, DAY) <= 30
            GROUP BY ufi.cohort_month, ufi.user_id, DATE_DIFF(DATE(i.timestamp), ufi.cohort_month, DAY)
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
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("tenant_id", "INT64", tenant_id),
                bigquery.ScalarQueryParameter("days_back", "INT64", days_back)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        return [dict(row) for row in results]