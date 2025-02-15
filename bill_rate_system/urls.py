from django.urls import path
from .views import upload_page,upload_temp_file,process_file ,list_projects,view_invoice,project_list,project_add,project_edit,timesheets,timesheet_detail,edit_timesheet_name

app_name="bill_rate_system"
urlpatterns = [
    path("", upload_page, name="upload-page"),
    path('upload_temp_file/', upload_temp_file, name='upload_temp_file'), 
    path('process_file/', process_file, name='process_file'),
    path('list_projects/', list_projects, name='list_projects'),
    path('projects/', project_list, name='project_list'),
    path('projects/add/',project_add, name='project_add'),
    path('projects/edit/<int:id>/',project_edit, name='project_edit'),
    path('timesheets/', timesheets, name='timesheets'),
    path('timesheets/<str:sheet_name>/', timesheet_detail, name='timesheet_detail'),
    path('timesheet/edit/<int:timesheet_id>/', edit_timesheet_name, name='edit_timesheet_name'),
    path('view_invoice/<str:project_name>/', view_invoice, name='view_invoice'),
]
