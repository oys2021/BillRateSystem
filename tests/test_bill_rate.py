import pytest
from django.contrib.auth.models import User
from django.urls import reverse
import os
import json
import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from bill_rate_system.models import Project, Timesheet
from django.contrib.messages import get_messages
from datetime import date, time




@pytest.mark.django_db
def test_upload_page(client):
    user = User.objects.create_user(username="testuser", password="testpassword")
    client.login(username="testuser", password="testpassword")
    response = client.get(reverse('bill_rate_system:upload-page'))
    assert response.status_code == 200 
    assert "text/html" in response["Content-Type"]
    


@pytest.mark.django_db
def test_upload_temp_file_valid_csv(client):
    Project.objects.create(name="Test Project")
    csv_content = b"Employee ID,Billable Rate,Project,Date,Start Time,End Time\n123,50,Test Project,2024-02-14,09:00,17:00"
    csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
    response = client.post(reverse('bill_rate_system:upload_temp_file'), {'file': csv_file})
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())  
    assert response.status_code == 200
    assert response.json()["message"] == "File uploaded successfully!"

    
@pytest.mark.django_db
def test_upload_temp_file_missing_file(client):
    """Test uploading without a file."""
    response = client.post(reverse('bill_rate_system:upload_temp_file'))

    assert response.status_code == 400
    assert "No file provided" in response.json()['error']
    

@pytest.mark.django_db
def test_upload_temp_file_invalid_extension(client):
    """Test uploading a non-CSV file."""
    txt_content = b"Invalid file content"
    txt_file = SimpleUploadedFile("test.txt", txt_content, content_type="text/plain")

    response = client.post(reverse('bill_rate_system:upload_temp_file'), {'file': txt_file})

    assert response.status_code == 400
    assert "Only CSV files are allowed" in response.json()['error']

@pytest.mark.django_db
def test_upload_temp_file_unregistered_project(client):
    csv_content = b"Employee ID,Billable Rate,Project,Date,Start Time,End Time\n123,50,Unknown Project,2024-02-14,09:00,17:00"
    csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

    response = client.post(reverse('bill_rate_system:upload_temp_file'), {'file': csv_file})

    assert response.status_code == 400
    assert "These projects are not registered" in response.json()['error']

@pytest.mark.django_db
def test_process_file(client):
    """Test processing a valid CSV file and storing timesheets."""
    project = Project.objects.create(name="Test Project")
    file_path = "uploads/test.csv"
    
    df = pd.DataFrame([{
        "Employee ID": 123, 
        "Billable Rate": 50, 
        "Project": "Test Project", 
        "Date": "2024-02-14", 
        "Start Time": "09:00", 
        "End Time": "17:00"
    }])
    df.to_csv(file_path, index=False)

    response = client.post(reverse('bill_rate_system:process_file'), json.dumps({"file_name": "test.csv"}), content_type="application/json")

    assert response.status_code == 200
    assert "File processed successfully!" in response.json()["message"]
    assert Timesheet.objects.count() == 1

    os.remove(file_path)

@pytest.mark.django_db
def test_process_file_missing_file(client):
    response = client.post(reverse('bill_rate_system:process_file'), json.dumps({"file_name": "nonexistent.csv"}), content_type="application/json")
    assert response.status_code == 400
    assert "File not found!" in response.json()['error']



@pytest.mark.django_db
def test_list_projects_with_data(client):
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_login(user) 
    session = client.session
    session["invoice_data"] = {
        "Test Project": [{"Employee ID": 123, "Total_Hours": 8, "Total_Cost": 400}]
    }
    session.save()
    response = client.get(reverse('bill_rate_system:list_projects'))
    print("Response Status Code:", response.status_code)
    print("Response Content:", response.content.decode())
    assert response.status_code == 200
    assert "Test Project" in response.content.decode()

@pytest.mark.django_db
def test_view_invoice_authenticated(client):
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_login(user)
    session = client.session
    session["invoice_data"] = {
        "Test Project": [
            {"Employee ID": 123, "Total_Hours": 8, "Unit_Price": 50, "Total_Cost": 400}
        ]
    }
    session.save()

    response = client.get(reverse("bill_rate_system:view_invoice", args=["Test Project"]))

    assert response.status_code == 200
    assert "Test Project" in response.content.decode()
    assert "123" in response.content.decode()  
    assert "400" in response.content.decode()  

@pytest.mark.django_db
def test_view_invoice_no_session_data(client):
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_login(user)
    response = client.get(reverse("bill_rate_system:view_invoice", args=["Test Project"]))
    assert response.status_code == 200
    assert "No invoice data found" in response.content.decode()

@pytest.mark.django_db
def test_view_invoice_project_not_found(client):
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_login(user)
    session = client.session
    session["invoice_data"] = {"Another Project": [{"Employee ID": 456, "Total_Hours": 5, "Total_Cost": 250}]}
    session.save()

    response = client.get(reverse("bill_rate_system:view_invoice", args=["Test Project"]))
    assert response.status_code == 200
    assert "No data found for project: Test Project" in response.content.decode()




@pytest.mark.django_db
def test_project_list_view(client):
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_login(user)
    project1 = Project.objects.create(name="Project A")
    project2 = Project.objects.create(name="Project B")

    response = client.get(reverse("bill_rate_system:project_list"))
    assert response.status_code == 200
    assert "Project A" in response.content.decode()
    assert "Project B" in response.content.decode()



@pytest.mark.django_db
def test_timesheets_view(client):
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_login(user)
    project = Project.objects.create(name="Test Project")
    Timesheet.objects.create(
        employee_id=1,
        project=project,
        date=date.today(),
        start_time=time(9, 0),
        end_time=time(17, 0),
        billable_rate=100.0,
        sheet_name="Sheet1",
    )
    Timesheet.objects.create(
        employee_id=2,
        project=project,
        date=date.today(),
        start_time=time(10, 0),
        end_time=time(18, 0),
        billable_rate=120.0,
        sheet_name="Sheet2",
    )
    Timesheet.objects.create(
        employee_id=3,
        project=project,
        date=date.today(),
        start_time=time(8, 0),
        end_time=time(16, 0),
        billable_rate=90.0,
        sheet_name="Sheet1",
    )
    response = client.get(reverse("bill_rate_system:timesheets"))
    assert response.status_code == 200
    assert "Sheet1" in response.content.decode()
    assert "Sheet2" in response.content.decode()



@pytest.mark.django_db
def test_edit_timesheet_name(client):
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_login(user)
    project = Project.objects.create(name="Test Project")
    timesheet=Timesheet.objects.create(
        employee_id=3,
        project=project,
        date=date.today(),
        start_time=time(8, 0),
        end_time=time(16, 0),
        billable_rate=90.0,
        sheet_name="Sheet1",
    )

    response = client.post(
        reverse("bill_rate_system:edit_timesheet_name", args=[timesheet.id]),
        {"sheet_name": "New Name"},
    )

    timesheet.refresh_from_db()
    assert timesheet.sheet_name == "New Name"

    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert "All timesheets with this name have been updated successfully!" in messages


@pytest.mark.django_db
def test_timesheet_detail_view(client):
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_login(user)
    project = Project.objects.create(name="Test Project")
    Timesheet.objects.create(
        employee_id=3,
        project=project,
        date=date.today(),
        start_time=time(8, 0),
        end_time=time(16, 0),
        billable_rate=90.0,
        sheet_name="Sheet1",
    )
    response = client.get(reverse("bill_rate_system:timesheet_detail", args=["Sheet1"]))

    assert response.status_code == 200
    assert "Sheet1" in response.content.decode()





@pytest.mark.django_db
def test_project_add(client):
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_login(user)
    response = client.post(reverse("bill_rate_system:project_add"), {"firstname": "New Project"})
    assert Project.objects.filter(name="New Project").exists()
    response = client.post(reverse("bill_rate_system:project_add"), {"firstname": "New Project"})
    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert "A project with this name already exists. Please choose a different name." in messages



@pytest.mark.django_db
def test_project_edit(client):
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_login(user)
    project = Project.objects.create(name="Old Project")

    response = client.post(reverse("bill_rate_system:project_edit", args=[project.id]), {"firstname": "Updated Project"})
    project.refresh_from_db()

    assert project.name == "Updated Project"
    assert response.status_code == 302 



