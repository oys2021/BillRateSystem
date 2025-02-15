import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages

@pytest.fixture
def user_data():
    return {
        "username": "testuser",
        "first_name": "Kwame",
        "last_name": "Doe",
        "email": "test@example.com",
        "password": "strongpassword123",
    }

@pytest.fixture
def create_user(user_data):
    return User.objects.create_user(**user_data)

@pytest.mark.django_db
def test_register_user(client, user_data):
    response = client.post(reverse("authentication:register"), {
        **user_data,
        "password1": user_data["password"],
        "password2": user_data["password"],
    })
    assert response.status_code == 302  
    user = User.objects.filter(username=user_data["username"]).first()
    assert user and user.first_name == user_data["first_name"]

@pytest.mark.django_db
def test_login_user(client, create_user, user_data):
    response = client.post(reverse("authentication:login"), {
        "username": user_data["username"],
        "password": user_data["password"],
    })
    assert response.status_code == 302  
    assert response.url == reverse("bill_rate_system:upload-page")  

@pytest.mark.django_db
def test_logout_user(client, create_user, user_data):
    client.login(username=user_data["username"], password=user_data["password"])
    response = client.get(reverse("authentication:logout"))
    assert response.status_code == 302  
    assert response.url == reverse("authentication:login")

@pytest.mark.django_db
def test_register_with_existing_username(client, create_user, user_data):
    response = client.post(reverse("authentication:register"), {
        **user_data,
        "email": "new@example.com",
        "password1": "anotherpassword123",
        "password2": "anotherpassword123",
    })
    assert response.status_code == 302  
    assert User.objects.filter(username=user_data["username"]).count() == 1  

@pytest.mark.django_db
def test_register_with_mismatched_passwords(client, user_data):
    response = client.post(reverse("authentication:register"), {
        **user_data,
        "password1": "password123",
        "password2": "differentpassword",
    }, follow=True)

    assert not User.objects.filter(username=user_data["username"]).exists()
    messages = [msg.message for msg in get_messages(response.wsgi_request)]
    assert any("Passwords do not match." in msg for msg in messages)

@pytest.mark.django_db
def test_login_invalid_credentials(client, create_user, user_data):
    response = client.post(reverse("authentication:login"), {
        "username": user_data["username"],
        "password": "wrongpassword",
    })
    assert response.status_code == 200  
    assert b"Invalid username or password" in response.content  
