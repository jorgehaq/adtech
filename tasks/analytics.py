from celery import shared_task
from django.db import connection
from tenacity import retry, stop_after_attempt, wait_exponential

@shared_task
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def calculate_daily_metrics(tenant_id):
    sql = """
    SELECT DATE(timestamp) as date, 
           COUNT(*) as impressions,
           SUM(cost) as total_cost,
           COUNT(DISTINCT user_id) as unique_users
    FROM campaigns_impression 
    WHERE tenant_id = %s
    GROUP BY DATE(timestamp)
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [tenant_id])
        return cursor.fetchall()