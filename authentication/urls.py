from django.urls import path
from .views import register_view, login_view,logout_view

app_name = "authentication"
urlpatterns = [
    path('', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
]
