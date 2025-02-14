import pytest
from django.contrib.auth.models import User
from django.urls import reverse

@pytest.mark.django_db
def test_upload_page(client):
    user = User.objects.create_user(username="testuser", password="testpassword")
    client.login(username="testuser", password="testpassword")
    response = client.get(reverse('bill_rate_system:upload-page'))
    assert response.status_code == 200 
    assert "text/html" in response["Content-Type"]
