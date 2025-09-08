import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from tasks.analytics import calculate_daily_metrics, process_events_batch, generate_campaign_report

# Test múltiples tenants
tenants = [1, 2, 3]
results = []

print("🚀 Testing Celery with multiple tenants...")

# Ejecutar tareas para cada tenant
for tenant_id in tenants:
    print(f"\n📊 Processing tenant {tenant_id}...")
    
    # Métricas diarias
    result1 = calculate_daily_metrics.delay(tenant_id)
    
    # Reporte de campaña (si existe campaña)
    result2 = generate_campaign_report.delay(tenant_id, 1, 'performance')
    
    results.append({
        'tenant_id': tenant_id,
        'metrics_task': result1,
        'report_task': result2
    })

# Esperar procesamiento
time.sleep(3)

# Verificar resultados
for result_set in results:
    tenant_id = result_set['tenant_id']
    print(f"\n✅ Tenant {tenant_id} Results:")
    print(f"   Metrics: {result_set['metrics_task'].status}")
    print(f"   Report: {result_set['report_task'].status}")
    
    if result_set['metrics_task'].status == 'SUCCESS':
        print(f"   Data: {result_set['metrics_task'].result}")

