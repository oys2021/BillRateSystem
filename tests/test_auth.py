import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages


@pytest.mark.django_db
def test_register_user(client):
    response = client.post(reverse('authentication:register'), {
        'username': 'testuser',
        'first_name': 'Kwame',
        'last_name': 'Doe',
        'email': 'test@example.com',
        'password1': 'strongpassword123',
        'password2': 'strongpassword123'
    })
    assert response.status_code == 302  
    
    user = User.objects.filter(username='testuser').first()
    assert user is not None
    assert user.first_name == "Kwame"
    assert user.last_name == "Doe"
    assert user.email == "test@example.com"


@pytest.mark.django_db
def test_login_user(client):
    user = User.objects.create_user(
        username='testuser',
        first_name='Kwame',
        last_name='Doe',
        email='test@example.com',
        password='strongpassword123'
    )

    response = client.post(reverse('authentication:login'), {
        'username': 'testuser',
        'password': 'strongpassword123'
    })
    
    assert response.status_code == 302  
    assert response.url == reverse('bill_rate_system:upload-page')  
    
    
@pytest.mark.django_db
def test_logout_user(client):
    user = User.objects.create_user(
        username='testuser',
        first_name='Kwame',
        last_name='Doe',
        email='test@example.com',
        password='strongpassword123'
    )

    client.login(username='testuser', password='strongpassword123')
    response = client.get(reverse('authentication:logout'))
    
    assert response.status_code == 302 
    assert response.url == reverse('authentication:login')


@pytest.mark.django_db
def test_register_with_existing_username(client):
    User.objects.create_user(
        username='testuser',
        first_name='Kwame',
        last_name='Doe',
        email='test@example.com',
        password='strongpassword123'
    )

    response = client.post(reverse('authentication:register'), {
        'username': 'testuser', 
        'first_name': 'Jane',
        'last_name': 'Doe',
        'email': 'new@example.com',
        'password1': 'anotherpassword123',
        'password2': 'anotherpassword123'
    })

    assert response.status_code == 302  
    assert User.objects.filter(username='testuser').count() == 1  




@pytest.mark.django_db
def test_register_with_mismatched_passwords(client):
    """Test registration fails when passwords don't match"""
    response = client.post(reverse('authentication:register'), {
        'username': 'newuser',
        'first_name': 'Kwame',
        'last_name': 'Doe',
        'email': 'new@example.com',
        'password1': 'password123',
        'password2': 'differentpassword'
    }, follow=True)  

    assert not User.objects.filter(username='newuser').exists()

    messages = list(get_messages(response.wsgi_request))
    assert any("Passwords do not match." in message.message for message in messages) 
 


@pytest.mark.django_db
def test_login_invalid_credentials(client):
    """Test login fails with incorrect credentials"""
    User.objects.create_user(
        username='testuser',
        first_name='Kwame',
        last_name='Doe',
        email='test@example.com',
        password='strongpassword123'
    )

    response = client.post(reverse('authentication:login'), {
        'username': 'testuser',
        'password': 'wrongpassword'
    })

    assert response.status_code == 200  
    assert b"Invalid username or password" in response.content  
