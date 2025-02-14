from django.shortcuts import render
from django.core.files.storage import default_storage
import pandas as pd 
import json
import os
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bill_rate_system.models import Timesheet,Project 
import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required(login_url='authentication:login')
def upload_page(request):
    return render(request, "bill_rate_system/upload.html")


@login_required(login_url='authentication:login')
def validate_row(row, index, required_columns, actual_column_count):
    errors = []

    if not isinstance(row['Employee ID'], (int, float)) or row['Employee ID'] <= 0:
        errors.append(f"Invalid Employee ID at row {index + 1}.")

    if not isinstance(row['Billable Rate'], (int, float)) or row['Billable Rate'] <= 0:
        errors.append(f"Invalid Billable Rate at row {index + 1}. Should be an Integer or Float.")

    date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m-%d-%Y']
    time_formats = ['%H:%M', '%I:%M %p']

    def parse_date(date_str):
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None 

    def parse_time(time_str):
        for fmt in time_formats:
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                continue
        return None 

    date = parse_date(str(row['Date']))
    if date is None:
        errors.append(f"Invalid Date format at row {index + 1}. Accepted formats: YYYY-MM-DD, DD/MM/YYYY, MM-DD-YYYY.")

    start_time = parse_time(str(row['Start Time']))
    end_time = parse_time(str(row['End Time']))

    if start_time is None:
        errors.append(f"Invalid Start Time format at row {index + 1}. Accepted formats: HH:MM (24-hour), HH:MM AM/PM.")
    if end_time is None:
        errors.append(f"Invalid End Time format at row {index + 1}. Accepted formats: HH:MM (24-hour), HH:MM AM/PM.")

    if start_time and end_time and end_time <= start_time:
        errors.append(f"End Time must be after Start Time at row {index + 1}.")

    return errors


@csrf_exempt
def upload_temp_file(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    if "file" not in request.FILES:
        return JsonResponse({"error": "No file provided"}, status=400)

    file = request.FILES["file"]

    if not file.name.endswith('.csv'):
        return JsonResponse({"error": "Only CSV files are allowed!"}, status=400)

    try:
        df = pd.read_csv(file)
        
        project_names = set(df['Project'].str.strip().str.title())

        existing_projects = set(Project.objects.values_list('name', flat=True))

        missing_projects = project_names - existing_projects
        
        if missing_projects:
            return JsonResponse({"error": f"Invalid file: These projects are not registered to the system {list(missing_projects)}, Please check for Project Spelling Errors or Add Project to the system"}, status=400)

        required_columns = ['Employee ID', 'Billable Rate', 'Project', 'Date', 'Start Time', 'End Time']
        extra_columns = [col for col in df.columns if col not in required_columns]

        if len(df.columns) > len(required_columns):
            return JsonResponse({
                "error": f"Unexpected extra columns detected: {', '.join(extra_columns)}"
            }, status=400)

        for column in required_columns:
            if column not in df.columns:
                return JsonResponse({"error": f" Missing required column: {column}"}, status=400)

        if df[required_columns].isnull().all().all():
            return JsonResponse({"error": "The uploaded file contains no data after the headers."}, status=400)

        missing_data_errors = []
        for column in required_columns:
            missing_rows = df[df[column].isna()].index.tolist()
            if missing_rows:
                missing_data_errors.append(f"Missing data in column '{column}' at rows: {', '.join(map(str, missing_rows))}")

        if missing_data_errors:
            return JsonResponse({"error": " | ".join(missing_data_errors)}, status=400)

        upload_dir = "uploads"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        file_path = os.path.join(upload_dir, file.name)
        with open(file_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        return JsonResponse({"message": "File uploaded successfully!", "file_name": file.name})

    except Exception as e:
        return JsonResponse({"error": f"File processing error: {str(e)}"}, status=400)


def generate_sheet_name():
    sheet_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))  
    return f"sheet{sheet_id}"



@csrf_exempt
def process_file(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Invalid request method"}, status=400)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

        file_name = data.get("file_name")
        sheet_name = generate_sheet_name()
        
        print(sheet_name)
        if not file_name:
            return JsonResponse({"error": "No file name provided"}, status=400)

        sheet_uploaded = Timesheet.objects.filter(sheet_name=sheet_name).exists()

        file_path = os.path.join("uploads", file_name)
        if not os.path.exists(file_path):
            return JsonResponse({"error": "File not found!"}, status=400)

        df = pd.read_csv(file_path)
        
        print(df)

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        new_entries = []
        for _, row in df.iterrows():
            try:
                project = Project.objects.get(name=row['Project'].strip().title())
                
                exists = Timesheet.objects.filter(
                    employee_id=row['Employee ID'],
                    project=project,
                    date=row['Date'],
                    start_time=row['Start Time'],
                    end_time=row['End Time']
                ).exists()

                if not exists:
                    new_entries.append(Timesheet(
                        employee_id=row['Employee ID'],
                        billable_rate=row['Billable Rate'],
                        project=project,
                        date=row['Date'],
                        start_time=row['Start Time'],
                        end_time=row['End Time'],
                        sheet_name=sheet_name  
                    ))
                    print("Doesnt Exist!!!")
                    print(new_entries)
                    
                    

            except Exception as row_error:
                print(f"Error processing row {row}: {row_error}")

        if new_entries:
            Timesheet.objects.bulk_create(new_entries)

        invoice_data = generate_invoice(df)
        request.session["invoice_data"] = invoice_data
        request.session.modified = True 
        
        sheet_name_message=f"the sheetname is {sheet_name}.You can change it later"
        
        if new_entries:
            return JsonResponse({
            "message": "File processed successfully!",
            "sheet_name":sheet_name_message,
            "redirect_url": "/list_projects/"
        })

       
        return JsonResponse({
            "message": "File processed successfully!",
            "sheet_name":"",
            "redirect_url": "/list_projects/"
        })


    except Exception as e:
        return JsonResponse({"error": f"Processing error: {str(e)}"}, status=400)


    
def generate_invoice(df):
    """
    Processes the DataFrame to calculate billable hours and generate invoices per project.
    """
    try:
        df['Start Time'] = pd.to_datetime(df['Start Time'], format='%H:%M').dt.time
        df['End Time'] = pd.to_datetime(df['End Time'], format='%H:%M').dt.time

        df['Hours Worked'] = df.apply(
            lambda row: (datetime.combine(datetime.min, row['End Time']) - 
                         datetime.combine(datetime.min, row['Start Time'])).seconds / 3600, axis=1)

        df['Cost'] = df['Hours Worked'] * df['Billable Rate']

        grouped = df.groupby(['Project', 'Employee ID']).agg(
            Total_Hours=('Hours Worked', 'sum'),
            Unit_Price=('Billable Rate', 'first'),
            Total_Cost=('Cost', 'sum')
        ).reset_index()

        
        invoice_data = {}
        for project, project_data in grouped.groupby('Project'):
            invoice_data[project] = project_data.to_dict(orient='records')

        return invoice_data  

    except Exception as e:
        return {"error": f"Invoice generation error: {str(e)}"}
    
    
def list_projects(request):
    invoice_data = request.session.get("invoice_data", {})

    if not invoice_data:
        return render(request, "bill_rate_system/invoices.html", {"error": "No invoice data found"})

    projects = list(invoice_data.keys())  

    return render(request, "bill_rate_system/list_projects.html", {"projects": projects})