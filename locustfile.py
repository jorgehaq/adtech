from locust import HttpUser, task, between, events
import os
import json
import time


class AuthenticatedUser(HttpUser):
    """Locust user that authenticates via JWT before running tasks."""

    wait_time = between(0.5, 2.5)

    def on_start(self):
        self.token = None
        self.headers = {"Content-Type": "application/json"}

        # Prefer login if provided; otherwise register a unique user
        email = os.getenv("LOCUST_EMAIL")
        username = os.getenv("LOCUST_USERNAME")
        password = os.getenv("LOCUST_PASSWORD", "testpass123")

        if email and username:
            # Try login (if your API supports it)
            login_payload = json.dumps({
                "email": email,
                "username": username,
                "password": password,
            })
            with self.client.post(
                "/api/v1/auth/login/",
                data=login_payload,
                headers=self.headers,
                catch_response=True,
            ) as resp:
                if resp.status_code == 200:
                    token = resp.json().get("access")
                    if token:
                        self.token = token
                        self.headers["Authorization"] = f"Bearer {self.token}"
                        resp.success()
                        return

        # Fallback: register a unique user for this Locust instance
        ts = int(time.time() * 1000)
        reg_payload = json.dumps({
            "email": f"locust-{ts}@test.com",
            "username": f"locustuser{ts}",
            "password": password,
            "tenant_id": int(os.getenv("LOCUST_TENANT_ID", "1")),
            "role": os.getenv("LOCUST_ROLE", "user"),
        })
        with self.client.post(
            "/api/v1/auth/register/",
            data=reg_payload,
            headers=self.headers,
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                token = resp.json().get("access")
                if token:
                    self.token = token
                    self.headers["Authorization"] = f"Bearer {self.token}"
                    resp.success()
                else:
                    resp.failure("No access token in register response")
            else:
                resp.failure(f"Register failed: {resp.status_code}")

    @task(3)
    def list_campaigns(self):
        self.client.get("/api/v1/campaigns/", headers=self.headers)

    @task(2)
    def list_ads(self):
        self.client.get("/api/v1/ads/", headers=self.headers)

    @task(2)
    def analytics_performance(self):
        self.client.get("/api/v1/analytics/performance/", headers=self.headers)

    @task(2)
    def analytics_cohorts(self):
        self.client.get("/api/v1/analytics/cohorts/", headers=self.headers)

    @task(1)
    def realtime_dashboard(self):
        self.client.get("/api/v1/analytics/realtime/dashboard/", headers=self.headers)


# Useful for headless CSV output: `locust --headless -u 50 -r 5 -t 2m -f locustfile.py --csv out --host http://localhost:8070`
