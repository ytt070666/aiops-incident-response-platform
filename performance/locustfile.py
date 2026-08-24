from locust import HttpUser, between, task

class AIopsUser(HttpUser):
    wait_time = between(0.2, 1)
    @task(3)
    def dashboard(self): self.client.get("/api/v1/dashboard", name="/dashboard")
    @task(2)
    def incidents(self): self.client.get("/api/v1/incidents", name="/incidents")
    @task(1)
    def diagnose(self): self.client.post("/api/v1/incidents/1/diagnose", name="/incidents/:id/diagnose")
