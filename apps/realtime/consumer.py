import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth import get_user_model
from apps.campaigns.models import Campaign
from django.db import connection

User = get_user_model()

class CampaignMetricsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.campaign_id = self.scope['url_route']['kwargs']['campaign_id']
        
        # JWT Authentication
        token = self.get_token_from_scope()
        self.user = await self.authenticate_token(token)
        
        if not self.user:
            await self.close(code=4001)
            return
            
        self.tenant_id = self.user.tenant_id
        self.room_group_name = f'campaign_{self.campaign_id}_tenant_{self.tenant_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Start real-time metrics
        self.metrics_task = asyncio.create_task(self.send_metrics_loop())

    async def disconnect(self, close_code):
        if hasattr(self, 'metrics_task'):
            self.metrics_task.cancel()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    def get_token_from_scope(self):
        query_string = self.scope.get('query_string', b'').decode()
        for param in query_string.split('&'):
            if param.startswith('token='):
                return param.split('=')[1]
        return None

    @database_sync_to_async
    def authenticate_token(self, token):
        if not token:
            return None
        try:
            UntypedToken(token)
            from rest_framework_simplejwt.authentication import JWTAuthentication
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token.encode())
            return jwt_auth.get_user(validated_token)
        except (InvalidToken, Exception):
            return None

    async def send_metrics_loop(self):
        while True:
            try:
                metrics = await self.get_real_time_metrics()
                await self.send(text_data=json.dumps({
                    'type': 'metrics_update',
                    'campaign_id': self.campaign_id,
                    'data': metrics,
                    'timestamp': asyncio.get_event_loop().time()
                }))
                await asyncio.sleep(3)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Metrics error: {str(e)}'
                }))
                break

    @database_sync_to_async
    def get_real_time_metrics(self):
        sql = """
        SELECT 
            COUNT(*) as impressions_last_hour,
            COUNT(DISTINCT ci.user_id) as unique_users,
            COALESCE(SUM(ci.cost), 0) as spend,
            COALESCE(AVG(ci.cost), 0) as avg_cpm,
            COUNT(*) / NULLIF(COUNT(DISTINCT ci.user_id), 0) as frequency
        FROM campaigns_impression ci
        JOIN campaigns_ad ad ON ci.ad_id = ad.id
        WHERE ad.campaign_id = %s 
        AND ci.tenant_id = %s
        AND ci.timestamp >= NOW() - INTERVAL 1 HOUR
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql, [self.campaign_id, self.tenant_id])
            row = cursor.fetchone()
            
            return {
                'impressions_last_hour': row[0] or 0,
                'unique_users': row[1] or 0,
                'total_spend': float(row[2] or 0),
                'avg_cpm': float(row[3] or 0),
                'frequency': float(row[4] or 0),
                'status': 'active' if (row[0] or 0) > 0 else 'idle'
            }

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        token = self.get_token_from_scope()
        self.user = await self.authenticate_token(token)
        
        if not self.user:
            await self.close(code=4001)
            return
            
        self.tenant_id = self.user.tenant_id
        self.room_group_name = f'dashboard_tenant_{self.tenant_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        self.dashboard_task = asyncio.create_task(self.send_dashboard_loop())

    async def disconnect(self, close_code):
        if hasattr(self, 'dashboard_task'):
            self.dashboard_task.cancel()
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    def get_token_from_scope(self):
        query_string = self.scope.get('query_string', b'').decode()
        for param in query_string.split('&'):
            if param.startswith('token='):
                return param.split('=')[1]
        return None

    @database_sync_to_async
    def authenticate_token(self, token):
        if not token:
            return None
        try:
            UntypedToken(token)
            from rest_framework_simplejwt.authentication import JWTAuthentication
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token.encode())
            return jwt_auth.get_user(validated_token)
        except (InvalidToken, Exception):
            return None

    async def send_dashboard_loop(self):
        while True:
            try:
                dashboard_data = await self.get_dashboard_metrics()
                await self.send(text_data=json.dumps({
                    'type': 'dashboard_update',
                    'data': dashboard_data,
                    'timestamp': asyncio.get_event_loop().time()
                }))
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception:
                break

    @database_sync_to_async
    def get_dashboard_metrics(self):
        sql = """
        SELECT 
            COUNT(DISTINCT ca.id) as active_campaigns,
            COUNT(ci.id) as total_impressions_today,
            COALESCE(SUM(ci.cost), 0) as total_spend_today,
            COUNT(DISTINCT ci.user_id) as unique_users_today
        FROM campaigns_campaign ca
        LEFT JOIN campaigns_ad ad ON ad.campaign_id = ca.id AND ad.tenant_id = %s
        LEFT JOIN campaigns_impression ci ON ci.ad_id = ad.id 
            AND ci.tenant_id = %s 
            AND DATE(ci.timestamp) = CURDATE()
        WHERE ca.tenant_id = %s AND ca.status = 'active'
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql, [self.tenant_id, self.tenant_id, self.tenant_id])
            row = cursor.fetchone()
            
            return {
                'active_campaigns': row[0] or 0,
                'impressions_today': row[1] or 0,
                'spend_today': float(row[2] or 0),
                'unique_users_today': row[3] or 0
            }