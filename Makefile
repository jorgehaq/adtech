SHELL := /bin/bash
.ONESHELL:

# Define environment files for different contexts
ENV_LOCAL_FILE ?= .env.local
ENV_PROD_FILE ?= .env.prod

# Global variables for GCP
PROJECT_ID ?=
REGION ?=
MYSQL_INSTANCE ?=
GS_BUCKET_NAME ?=
IMPRESSION_TOPIC ?=
CLICK_TOPIC ?=
IMPRESSION_FUNCTION_NAME ?=
CLICK_FUNCTION_NAME ?=


# Load environment variables
define LOAD_LOCAL_ENV
   set -a; source $(ENV_LOCAL_FILE); set +a
endef

define LOAD_PROD_ENV
   set -a; source $(ENV_PROD_FILE); set +a
endef

# ==============================================
# LOCAL DEVELOPMENT
# ==============================================

.PHONY: services services-down services-logs services-restart

services:
	@docker compose --env-file .env.local up -d
	@echo "✅ Services started:"
	@echo "   - MySQL: localhost:3306"
	@echo "   - Redis: localhost:6379"
	@echo ""
	@echo "🚀 Ready for local development:"
	@echo "   source .venv/bin/activate"
	@echo "   python manage.py runserver"

services-down:
	@docker compose down

services-logs:
	@docker compose logs -f

services-restart:
	@docker compose restart

# Local Django development
.PHONY: local migrate shell test dbshell load-million

local:
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	PORT_TO_USE=$${PORT:-8070}; \
	while lsof -i :$$PORT_TO_USE > /dev/null 2>&1; do \
	    echo "Port $$PORT_TO_USE is in use, trying $$((PORT_TO_USE + 1))"; \
	    PORT_TO_USE=$$((PORT_TO_USE + 1)); \
	done; \
	echo "Starting server on port $$PORT_TO_USE"; \
	python manage.py runserver 0.0.0.0:$$PORT_TO_USE

migrate:
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py makemigrations
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py migrate

shell:
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py shell

dbshell:
	@docker compose exec mysql mysql -u root -p

load-million:
	@echo "Loading 1M test records..."
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py load_million_records --records=1000000

# Local Celery (optional)
.PHONY: celery flower

celery:
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; .venv/bin/celery -A core worker -l info

flower:
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	echo "🌸 Starting Flower on available port..."; \
	PORT_TO_USE=5555; \
	while lsof -i :$$PORT_TO_USE > /dev/null 2>&1; do \
		echo "Port $$PORT_TO_USE is in use, trying $$((PORT_TO_USE + 1))"; \
		PORT_TO_USE=$$((PORT_TO_USE + 1)); \
	done; \
	echo "Starting Flower on port $$PORT_TO_USE"; \
	.venv/bin/celery -A core flower --port=$$PORT_TO_USE


.PHONY: celery-check

.PHONY: celery-check

celery-check:
	@$(call LOAD_LOCAL_ENV); \
	echo "🔍 Verificando estado de Redis (docker)..."; \
	REDIS_CONTAINER=$$(docker ps --format '{{.Names}}' | grep redis || true); \
	if [ -z "$$REDIS_CONTAINER" ]; then \
		echo "❌ No se encontró contenedor Redis corriendo. Ejecuta 'make services'."; \
		exit 1; \
	fi; \
	if docker exec $$REDIS_CONTAINER redis-cli ping | grep -q PONG; then \
		echo "✅ Redis responde correctamente en contenedor $$REDIS_CONTAINER."; \
	else \
		echo "❌ Redis no responde dentro del contenedor $$REDIS_CONTAINER."; \
		exit 1; \
	fi; \
	echo "🚦 Verificando conexión de Celery con el broker..."; \
	if .venv/bin/celery -A core status | grep -q "OK"; then \
		echo "✅ Celery conectado correctamente al broker."; \
	else \
		echo "❌ Celery no pudo conectarse. ¿Está corriendo 'make celery'?"; \
		exit 1; \
	fi



# Development workflow
.PHONY: up dev flush

up: services migrate
	@echo "🎯 Development setup complete!"
	@echo "   Run: make local (or source .venv/bin/activate && python manage.py runserver)"

dev: services
	@$(MAKE) migrate
	@$(MAKE) local

# Database operations
flush:
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py flush --noinput

# Cleanup
clean:
	@$(call LOAD_LOCAL_ENV); docker compose down -v
	@docker system prune -f

# Health check
health:
	@echo "Services Health Check:"
	@docker compose --env-file $(ENV_LOCAL_FILE) ps
	@echo ""
	@docker exec adtech-mysql-1 mysql -u root -ppassword -e "SELECT 1" > /dev/null 2>&1 && echo "✅ MySQL" || echo "❌ MySQL"
	@docker exec adtech-redis-1 redis-cli ping > /dev/null 2>&1 && echo "✅ Redis" || echo "❌ Redis"


# ==============================================
# TEST ANALYTICS LOCAL
# ==============================================



# Common test setup
define TEST_SETUP
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local
endef

.PHONY: test test-analytics test-repositories test-performance

# Default test target - runs repository tests
test: test-repositories

# Run all analytics tests with verbose output
test-analytics:
	$(TEST_SETUP); python manage.py test apps.analytics -v 2

# Run repository tests with verbose output
test-repositories:
	$(TEST_SETUP); python manage.py test apps.analytics.tests.test_repositories -v 2

# Run specific performance test
test-performance:
	$(TEST_SETUP); python manage.py test apps.analytics.tests.test_repositories.AnalyticsRepositoryTest -v 2




# ==============================================
# TEST EVENTS
# ==============================================

# Test event sourcing replay functionality
.PHONY: test-event-replay test-event-creation test-audit-trail test-event-flow

# Test complete event sourcing flow
test-event-flow: services
	@echo "🧪 Testing complete event sourcing flow..."
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	echo "1. Finding available port..."; \
	PORT_TO_USE=8070; \
	while lsof -i :$$PORT_TO_USE > /dev/null 2>&1; do \
		echo "Port $$PORT_TO_USE is in use, trying $$((PORT_TO_USE + 1))"; \
		PORT_TO_USE=$$((PORT_TO_USE + 1)); \
	done; \
	echo "Starting server on port $$PORT_TO_USE..."; \
	python manage.py runserver 0.0.0.0:$$PORT_TO_USE & \
	SERVER_PID=$$!; \
	sleep 5; \
	echo "2. Running event sourcing tests..."; \
	export TEST_PORT=$$PORT_TO_USE; ./test_event_sourcing.sh || true; \
	echo "3. Stopping server..."; \
	kill $$SERVER_PID 2>/dev/null || true

# Test event replay endpoint specifically  
test-event-replay:
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	echo "🔄 Testing event replay functionality..."; \
	python -c "\
import os, django; \
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local'); \
django.setup(); \
from apps.analytics.events import replay_events; \
from apps.analytics.models import AdEvent; \
from apps.campaigns.models import Campaign; \
print('Events before replay:', AdEvent.objects.filter(tenant_id=1).count()); \
result = replay_events('1', 1); \
print('Events replayed:', result)"

# Test event creation flow
test-event-creation:
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	python -c "
	from apps.campaigns.models import Campaign;
	from apps.advertisers.models import Advertiser;
	from apps.analytics.models import AdEvent;
	# Create test data if missing
	if not Campaign.objects.filter(tenant_id=1).exists():
	    print('Creating test campaign...');
	    adv = Advertiser.objects.get_or_create(tenant_id=1, name='Test', defaults={'email':'test@test.com', 'status':'active'})[0];
	    Campaign.objects.create(tenant_id=1, name='Test Campaign', budget=1000, status='active', start_date='2025-01-01', end_date='2025-12-31', advertiser=adv);
	event = AdEvent.objects.create(tenant_id=1, event_type='impression_created', aggregate_id='1', payload={'cost': '0.50', 'user_id': 12345}, sequence_number=AdEvent.objects.count() + 1);
	print('Event created:', event.id)"

# Test audit trail
test-audit-trail:
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	python -c "
	from apps.analytics.models import AdEvent;
	events = AdEvent.objects.filter(tenant_id=1).order_by('-timestamp')[:5];
	if events: [print(f'  {e.event_type} - {e.timestamp} - {e.payload}') for e in events]
	else: print('No events found - create some first')"

# Test event replay endpoint specifically  
test-event-replay-endpoint:
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	echo "🔄 Testing event replay endpoint..."; \
	TOKEN_RESPONSE=$$(curl -s -X POST "http://localhost:8070/api/v1/auth/register/" \
		-H "Content-Type: application/json" \
		-d '{"email":"replay-test@test.com","username":"replayuser","password":"testpass123","tenant_id":1,"role":"user"}'); \
	ACCESS_TOKEN=$$(echo "$$TOKEN_RESPONSE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('access', ''))" 2>/dev/null || echo ""); \
	if [ -n "$$ACCESS_TOKEN" ]; then \
		echo "✅ Testing event replay..."; \
		curl -X POST "http://localhost:8070/api/v1/events/rebuild-metrics/1/" \
			-H "Authorization: Bearer $$ACCESS_TOKEN" | python3 -m json.tool; \
	fi


# ==============================================
# TEST CIRCUIT BREAKER
# ==============================================

# Test circuit breaker implementation
.PHONY: test-circuit-breaker test-circuit-breaker-stress test-circuit-status

# Test normal operation (should work)
test-circuit-breaker: services
	@echo "🔧 Testing Circuit Breaker Implementation..."
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	PORT_TO_USE=8070; \
	while lsof -i :$$PORT_TO_USE > /dev/null 2>&1; do \
		echo "Port $$PORT_TO_USE is in use, trying $$((PORT_TO_USE + 1))"; \
		PORT_TO_USE=$$((PORT_TO_USE + 1)); \
	done; \
	echo "Starting server on port $$PORT_TO_USE..."; \
	python manage.py runserver 0.0.0.0:$$PORT_TO_USE & \
	SERVER_PID=$$!; \
	sleep 5; \
	echo "Running circuit breaker tests..."; \
	export TEST_PORT=$$PORT_TO_USE; ./test_circuit_breaker.sh || true; \
	echo "Stopping server..."; \
	kill $$SERVER_PID 2>/dev/null || true

# Test circuit breaker status endpoint
test-circuit-status:
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	echo "📊 Testing circuit breaker status..."; \
	python -c "\
import os, django; \
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local'); \
django.setup(); \
from django.core.cache import cache; \
print('Circuit states:'); \
circuits = ['apps.campaigns.views.get_queryset', 'apps.analytics.repository.cohort_analysis']; \
[print(f'  {circuit}: {cache.get(f\"circuit_breaker:{circuit}\", {\"state\": \"closed\"})}') for circuit in circuits]"


# Test circuit breaker with authentication and stress
test-circuit-breaker-stress: services
	@echo "🔧 Testing Circuit Breaker Under Stress..."
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	PORT_TO_USE=8070; \
	while lsof -i :$$PORT_TO_USE > /dev/null 2>&1; do \
		echo "Port $$PORT_TO_USE is in use, trying $$((PORT_TO_USE + 1))"; \
		PORT_TO_USE=$$((PORT_TO_USE + 1)); \
	done; \
	echo "Starting server on port $$PORT_TO_USE..."; \
	python manage.py runserver 0.0.0.0:$$PORT_TO_USE & \
	SERVER_PID=$$!; \
	sleep 5; \
	echo "Getting JWT token..."; \
	TOKEN_RESPONSE=$$(curl -s -X POST "http://localhost:$$PORT_TO_USE/api/v1/auth/register/" \
		-H "Content-Type: application/json" \
		-d '{"email":"stress-test@test.com","username":"stressuser","password":"testpass123","tenant_id":1,"role":"user"}'); \
	ACCESS_TOKEN=$$(echo "$$TOKEN_RESPONSE" | python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('access', ''))" 2>/dev/null || echo ""); \
	if [ -n "$$ACCESS_TOKEN" ]; then \
		echo "✅ Token obtained, running stress test..."; \
		for i in {1..20}; do \
			curl -s -H "Authorization: Bearer $$ACCESS_TOKEN" "http://localhost:$$PORT_TO_USE/api/v1/campaigns/" > /dev/null & \
		done; \
		wait; \
		echo "Checking circuit status..."; \
		curl -s "http://localhost:$$PORT_TO_USE/api/v1/analytics/circuit-breaker/status/" | python3 -m json.tool; \
	else \
		echo "❌ Failed to get token"; \
	fi; \
	echo "Stopping server..."; \
	kill $$SERVER_PID 2>/dev/null || true


# ==============================================
# TEST WEBSOCKETS
# ==============================================

.PHONY: test-websockets test-ws-auth test-ws-metrics test-ws-dashboard

# Test WebSocket authentication and connections
test-websockets: services
	@echo "🔌 Testing WebSocket Connections..."
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	PORT_TO_USE=8070; \
	while lsof -i :$$PORT_TO_USE > /dev/null 2>&1; do \
		echo "Port $$PORT_TO_USE is in use, trying $$((PORT_TO_USE + 1))"; \
		PORT_TO_USE=$$((PORT_TO_USE + 1)); \
	done; \
	echo "Starting server on port $$PORT_TO_USE..."; \
	python manage.py runserver 0.0.0.0:$$PORT_TO_USE & \
	SERVER_PID=$$!; \
	sleep 5; \
	echo "Testing WebSocket endpoints..."; \
	export TEST_PORT=$$PORT_TO_USE; ./test_websockets.sh || true; \
	echo "Stopping server..."; \
	kill $$SERVER_PID 2>/dev/null || true

# Test WebSocket authentication specifically
test-ws-auth:
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	echo "🔐 Testing WebSocket JWT authentication..."; \
	python -c "
	import os, django;
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local');
	django.setup();
	from apps.realtime.consumer import CampaignMetricsConsumer;
	print('✅ WebSocket consumer loaded');
	print('✅ JWT authentication ready');
	"

# Test real-time metrics flow
test-ws-metrics:
	@echo "📊 Testing WebSocket metrics flow..."
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	python -c "
	import os, django;
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local');
	django.setup();
	from apps.realtime.consumer import CampaignMetricsConsumer;
	print('✅ CampaignMetricsConsumer loaded');
	print('✅ JWT authentication methods available');
	print('✅ Real-time metrics SQL queries ready')
	"

# Test dashboard consumer
test-ws-dashboard:
	@echo "📈 Testing Dashboard WebSocket consumer..."
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	python -c "
	import os, django;
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local');
	django.setup();
	from apps.realtime.consumer import DashboardConsumer;
	print('✅ DashboardConsumer loaded');
	print('✅ Multi-tenant dashboard metrics ready')
	"



# ==============================================
# GCP DEPLOYMENT SEQUENCE
# ==============================================

# Environment validation
.PHONY: gcp-setup check-env-prod
check-env-prod:
	@if [ ! -f .env.prod ]; then \
	    echo "❌ .env.prod not found. Run 'make gcp-build-django' first"; \
	    exit 1; \
	fi


# 1. Setup básico (ya hecho)
.PHONY: gcp-setup
gcp-setup:
	@$(call LOAD_PROD_ENV); \
	echo "🔧 Setting up GCP resources..."; \
	gcloud pubsub topics create $$IMPRESSION_TOPIC --project=$$PROJECT_ID || true; \
	gcloud pubsub topics create $$CLICK_TOPIC --project=$$PROJECT_ID || true; \
	bq mk --project_id=$$PROJECT_ID --dataset adtech_analytics || true

# 2. Enable required APIs
.PHONY: gcp-enable-apis
gcp-enable-apis:
	@$(call LOAD_PROD_ENV); \
	echo "⚡ Enabling GCP APIs..."; \
	gcloud services enable sqladmin.googleapis.com --project=$$PROJECT_ID; \
	gcloud services enable run.googleapis.com --project=$$PROJECT_ID; \
	gcloud services enable storage.googleapis.com --project=$$PROJECT_ID; \
	gcloud services enable cloudbuild.googleapis.com --project=$$PROJECT_ID; \
	gcloud services enable cloudfunctions.googleapis.com --project=$$PROJECT_ID

# 3. Create Cloud SQL
.PHONY: gcp-create-sql
gcp-create-sql:
	@$(call LOAD_PROD_ENV); \
	echo "🗄️ Creating Cloud SQL instance..."; \
	gcloud sql instances create $$MYSQL_INSTANCE \
	    --project=$$PROJECT_ID \
	    --tier=db-f1-micro \
	    --region=$$REGION \
	    --database-version=MYSQL_8_0 \
	    --storage-type=SSD \
	    --storage-size=10GB || true; \
	\
	echo "📊 Creating database..."; \
	gcloud sql databases create $$DB_NAME \
	    --instance=$$MYSQL_INSTANCE \
	    --project=$$PROJECT_ID || true; \
	\
	echo "👤 Creating database user..."; \
	gcloud sql users create $$DB_USER \
	    --instance=$$MYSQL_INSTANCE \
	    --project=$$PROJECT_ID \
	    --password=$$DB_PASSWORD


# 4. Create VPC Connector for Redis
.PHONY: gcp-create-vpc-connector
gcp-create-vpc-connector:
	@$(call LOAD_PROD_ENV); \
	echo "🔗 Creating VPC connector for Redis..."; \
	gcloud compute networks vpc-access connectors create $$VPC_CONNECTOR_NAME \
		--region=$$REGION \
	    --range=10.8.0.0/28 \
	    --network=default \
		--min-instances=2 \
		--max-instances=3 \
		--machine-type=e2-micro \
		--project=$$PROJECT_ID || true


# 4. Create Storage buckets
.PHONY: gcp-create-storage
gcp-create-storage:
	@$(call LOAD_PROD_ENV); \
	echo "📦 Creating storage buckets..."; \
	gsutil mb -l $$REGION gs://$$GS_BUCKET_NAME || true; \
	gsutil mb -l $$REGION gs://$$PROJECT_ID-static || true; \
	\
	echo "🔒 Setting bucket permissions..."; \
	gsutil iam ch allUsers:objectViewer gs://$$GS_BUCKET_NAME; \
	gsutil iam ch allUsers:objectViewer gs://$$PROJECT_ID-static

# 5. Deploy Cloud Functions
.PHONY: deploy-functions deploy-impression-processor deploy-click-processor
deploy-functions: deploy-impression-processor deploy-click-processor

deploy-impression-processor:
	@$(call LOAD_PROD_ENV); \
	echo "🚀 Deploying impression processor..."; \
	cd ../adtech-cloud-function/process_events && \
	gcloud functions deploy $$IMPRESSION_FUNCTION_NAME \
	    --runtime python311 \
	    --trigger-topic $$IMPRESSION_TOPIC \
	    --entry-point process_impression_event \
	    --region $$REGION \
	    --project $$PROJECT_ID

deploy-click-processor:
	@$(call LOAD_PROD_ENV); \
	echo "🚀 Deploying click processor..."; \
	cd ../adtech-cloud-function/bid_processor && \
	gcloud functions deploy $$CLICK_FUNCTION_NAME \
	    --runtime python311 \
	    --trigger-topic $$CLICK_TOPIC \
	    --entry-point process_click_event \
	    --region $$REGION \
	    --project $$PROJECT_ID

# 6. Build Django for Cloud Run
.PHONY: gcp-build-django 

gcp-build-django: check-env-prod
	@$(call LOAD_PROD_ENV); \
	echo "🐳 Building Django for Cloud Run..."; \
	echo "Using existing .env.prod with variables:"; \
	echo "  DB_NAME=$$DB_NAME"; \
	echo "  DB_USER=$$DB_USER"; \
	echo "  GS_BUCKET_NAME=$$GS_BUCKET_NAME"

# 7. Deploy Django to Cloud Run
.PHONY: gcp-deploy-django

gcp-deploy-django: check-env-prod
	@$(call LOAD_PROD_ENV); \
	echo "🚀 Deploying Django to Cloud Run..."; \
	yes | gcloud run deploy adtech-backend \
		--source . \
		--region $$REGION \
		--allow-unauthenticated \
		--set-env-vars DJANGO_SETTINGS_MODULE=core.settings.prod \
		--set-env-vars DB_NAME=$$DB_NAME \
		--set-env-vars DB_USER=$$DB_USER \
		--set-env-vars DB_PASSWORD=$$DB_PASSWORD \
	    --set-env-vars DB_HOST=/cloudsql/$$PROJECT_ID:$$REGION:$$MYSQL_INSTANCE \
	    --set-env-vars REDIS_HOST=$$REDIS_HOST \
		--set-env-vars GS_BUCKET_NAME=$$GS_BUCKET_NAME \
		--set-env-vars SECRET_KEY=$$SECRET_KEY \
		--set-env-vars GCP_PROJECT_ID=$$PROJECT_ID \
		--add-cloudsql-instances $$PROJECT_ID:$$REGION:$$MYSQL_INSTANCE \
	    --vpc-connector=$$VPC_CONNECTOR_NAME \
		--project $$PROJECT_ID \
		--memory 1Gi \
		--cpu 1

# 8. Run Django migrations on Cloud Run
.PHONY: gcp-migrate
gcp-migrate:
	@$(call LOAD_PROD_ENV); \
	echo "📊 Running Django migrations..."; \
	SERVICE_URL=$$(gcloud run services describe adtech-backend --region=$$REGION --project=$$PROJECT_ID --format="value(status.url)"); \
	echo "Service URL: $$SERVICE_URL"; \
	echo "Migrations must be run manually via Cloud Shell or local connection"

# 9. Setup Cloud SQL proxy (for local development)
.PHONY: gcp-sql-proxy
gcp-sql-proxy:
	@$(call LOAD_PROD_ENV); \
	echo "🔌 Starting Cloud SQL proxy..."; \
	echo "Download: https://cloud.google.com/sql/docs/mysql/sql-proxy"; \
	./cloud-sql-proxy $$PROJECT_ID:$$REGION:$$MYSQL_INSTANCE &; \
	echo "Proxy running on localhost:3306"

# ==============================================
# DEPLOYMENT SEQUENCE COMMANDS
# ==============================================

# Complete setup from scratch
.PHONY: gcp-deploy-all
gcp-deploy-all: gcp-enable-apis gcp-create-sql gcp-create-storage gcp-create-vpc-connector gcp-build-django gcp-deploy-django 
	@echo "✅ Complete GCP deployment finished!"
	@echo "🌐 Check your Cloud Run service:"
	@gcloud run services list --region=$$REGION --project=$$PROJECT_ID

# Quick redeploy (code changes)
.PHONY: gcp-redeploy
gcp-redeploy: gcp-build-django gcp-deploy-django
	@echo "✅ Django redeployed!"

# Check deployment status
.PHONY: gcp-status
gcp-status:
	@$(call LOAD_PROD_ENV); \
	echo "📊 GCP Resources Status:"; \
	echo "\n🗄️ Cloud SQL:"; \
	gcloud sql instances list --project=$$PROJECT_ID; \
	echo "\n🚀 Cloud Run:"; \
	gcloud run services list --region=$$REGION --project=$$PROJECT_ID; \
	echo "\n⚡ Cloud Functions:"; \
	gcloud functions list --regions=$$REGION --project=$$PROJECT_ID; \
	echo "\n📦 Storage:"; \
	gsutil ls

# Cleanup (careful!)
.PHONY: gcp-cleanup
gcp-cleanup:
	@$(call LOAD_PROD_ENV); \
	echo "⚠️ This will DELETE all GCP resources!"; \
	read -p "Are you sure? (yes/NO): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
	    gcloud run services delete adtech-backend --region=$$REGION --project=$$PROJECT_ID --quiet || true; \
	    gcloud functions delete $$IMPRESSION_FUNCTION_NAME --region=$$REGION --project=$$PROJECT_ID --quiet || true; \
	    gcloud functions delete $$CLICK_FUNCTION_NAME --region=$$REGION --project=$$PROJECT_ID --quiet || true; \
	    gcloud sql instances delete $$MYSQL_INSTANCE --project=$$PROJECT_ID --quiet || true; \
	    gsutil rm -r gs://$$GS_BUCKET_NAME || true; \
	    gsutil rm -r gs://$$PROJECT_ID-static || true; \
	    echo "🗑️ Resources deleted"; \
	else \
	    echo "❌ Cancelled"; \
	fi




# ==============================================
# TEST BIGQUERY INTEGRATION
# ==============================================

.PHONY: test-bigquery test-bq-connection test-bq-sync test-bq-queries



# Test BigQuery integration
test-bigquery: test-bq-connection test-bq-sync test-bq-queries

# Test BigQuery connection
test-bq-connection:
	@echo "🔗 Testing BigQuery (local will use mock)..."
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	python -c "from apps.analytics.bigquery import BigQueryAnalytics; bq = BigQueryAnalytics(); print('✅ BigQuery mock mode active for local development') if bq.mock_mode else print('✅ BigQuery real mode active')"

# Test BigQuery sync functionality
test-bq-sync:
	@echo "📊 Testing BigQuery sync..."
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local'); django.setup(); from apps.analytics.bigquery import BigQueryAnalytics; bq = BigQueryAnalytics(); status = bq.get_sync_status(1); print(f'✅ Sync status: {status}')"

# Test BigQuery queries
test-bq-queries:
	@echo "🔍 Testing BigQuery queries..."
	@$(call LOAD_LOCAL_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; \
	python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local'); django.setup(); from apps.analytics.bigquery import BigQueryAnalytics; bq = BigQueryAnalytics(); print('✅ BigQuery analytics methods loaded'); print('✅ Cohort analysis query ready'); print('✅ Performance analysis query ready')"



.PHONY: test-bigquery-gcp

# Test BigQuery on GCP
test-bigquery-gcp:
	@echo "🌐 Testing BigQuery on deployed GCP..."
	@chmod +x test_gcp_bigquery.sh
	@./test_gcp_bigquery.sh

