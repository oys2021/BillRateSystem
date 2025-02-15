import pytest
from django.contrib.auth.models import User
from django.urls import reverse
import os
import json
import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from bill_rate_system.models import Project, Timesheet



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


from django.contrib.auth import get_user_model

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



# @pytest.mark.django_db
# def test_list_projects_no_data(client):
#     """Test listing projects when there is no invoice data."""
#     response = client.get(reverse('bill_rate_system:list-projects'))

#     assert response.status_code == 200
#     assert "No invoice data found" in response.content.decode()

import pytest
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_view_invoice_authenticated(client):
    # Create and login user
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_login(user)

    # Simulate session data
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




