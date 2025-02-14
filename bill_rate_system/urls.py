from django.urls import path
from .views import upload_page,process_file,upload_temp_file,list_projects

app_name="bill_rate_system"
urlpatterns = [
    path("", upload_page, name="upload-page"),
    path('upload_temp_file/', upload_temp_file, name='upload_temp_file'), 
    path('process_file/', process_file, name='process_file'),
    path('list_projects/', list_projects, name='list_projects'),
]
