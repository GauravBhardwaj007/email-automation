from locust import HttpUser, task, between
import json

class StreamlitUser(HttpUser):
    wait_time = between(1, 5)  # Random wait time between tasks

    # Custom headers to simulate POST request to Streamlit
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Content-Type": "application/json"
    }

    def on_start(self):
        """This function is called once before each user starts."""
        # Simulate login by sending the login credentials
        login_payload = {
            "username": "admin",  # Replace with valid username
            "password": "admin123"  # Replace with valid password
        }
        # Simulate login POST request
        response = self.client.post("http://localhost:8501/", json=login_payload, headers=self.headers)

        # Capture session cookie after login
        self.session_cookie = response.cookies.get('ajs_anonymous_id')  # Capture session cookie
        self.xsrf_token = response.cookies.get('_streamlit_xsrf')  # Capture CSRF token (if needed)

    @task(3)  # Simulate email scheduling submission
    def submit_email(self):
        """Simulate submitting the email form"""
        email_payload = {
            "email": "gawrvbhardwaj@gmail.com",  # Replace with the email being scheduled
            "time": "2024-12-01T18:00"  # Adjust this based on the actual data in your form
        }
        # Simulate sending the email (this doesn't actually send it through an SMTP server in the test)
        self.client.post(
            "http://localhost:8501/",  # Adjust URL if needed (for the form submission)
            json=email_payload,
            cookies={"ajs_anonymous_id": self.session_cookie, "_streamlit_xsrf": self.xsrf_token},  # Include cookies for session handling
            headers=self.headers
        )

    @task  # Simulate visiting the home page
    def load_homepage(self):
        """Simulate visiting the home page"""
        self.client.get(
            "http://localhost:8501/",  # URL for the home page
            cookies={"ajs_anonymous_id": self.session_cookie, "_streamlit_xsrf": self.xsrf_token},  # Include cookies for session handling
            headers=self.headers
        )
