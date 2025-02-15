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
import logging
logger = logging.getLogger('views_logger')


@login_required(login_url='authentication:login')
def upload_page(request):
    logger.info(f"User {request.user} accessed the upload page.")
    return render(request, "bill_rate_system/upload.html")



def validate_row(row, index, required_columns, actual_column_count):
    errors = []
    
    if len(row) != actual_column_count:
        errors.append(f"Row {index + 1}: Incorrect number of columns.")

    try:
        employee_id = float(row['Employee ID'])  #
        if employee_id <= 0 or not employee_id.is_integer():
            errors.append(f"Row {index + 1}: Invalid Employee ID ({row['Employee ID']}).")
    except ValueError:
        errors.append(f"Row {index + 1}: Invalid Employee ID ({row['Employee ID']}).")
        
    try:
        billable_rate = float(row['Billable Rate'])  
        if billable_rate <= 0:
            errors.append(f"Row {index + 1}: Invalid Billable Rate ({row['Billable Rate']}).")
    except ValueError:
        errors.append(f"Row {index + 1}: Invalid Billable Rate ({row['Billable Rate']}).")

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
            return JsonResponse({"error": f"Invalid file: These projects/companies are not registered to the system {list(missing_projects)}, Please check for Project Spelling Errors or Add Project to the system"}, status=400)

        required_columns = ['Employee ID', 'Billable Rate', 'Project', 'Date', 'Start Time', 'End Time']
        extra_columns = [col for col in df.columns if col not in required_columns]

        if len(df.columns) > len(required_columns):
            return JsonResponse({
                "error": f"Unexpected extra columns detected: {', '.join(extra_columns)}"
            }, status=400)
            
        validation_errors = []
        for index, row in df.head(10).iterrows():
            errors = validate_row(row, index, required_columns, len(df.columns))
            if errors:
                validation_errors.extend(errors)

        if validation_errors:
            return JsonResponse({"error": validation_errors}, status=400)
            
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
        logger.info("Processing file request received.")

        if request.method != "POST":
            logger.warning("Invalid request method: %s", request.method)
            return JsonResponse({"error": "Invalid request method"}, status=400)

        try:
            data = json.loads(request.body)
            logger.info("Request JSON successfully parsed.")
        except json.JSONDecodeError:
            logger.error("Invalid JSON data received.")
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

        file_name = data.get("file_name")
        sheet_name = generate_sheet_name()
        logger.info(f"Generated sheet name: {sheet_name}")

        if not file_name:
            logger.warning("No file name provided in request.")
            return JsonResponse({"error": "No file name provided"}, status=400)

        file_path = os.path.join("uploads", file_name)
        if not os.path.exists(file_path):
            logger.error(f"File not found at path: {file_path}")
            return JsonResponse({"error": "File not found!"}, status=400)

        df = pd.read_csv(file_path)
        logger.info("CSV file loaded successfully.")

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
                    new_entry = Timesheet(
                        employee_id=row['Employee ID'],
                        billable_rate=row['Billable Rate'],
                        project=project,
                        date=row['Date'],
                        start_time=row['Start Time'],
                        end_time=row['End Time'],
                        sheet_name=sheet_name  
                    )
                    new_entries.append(new_entry)
                    logger.info(f"New entry added for Employee ID: {row['Employee ID']} on {row['Date']}.")

            except Exception as row_error:
                logger.error(f"Error processing row {row.to_dict()}: {row_error}", exc_info=True)

        if new_entries:
            Timesheet.objects.bulk_create(new_entries)
            logger.info(f"{len(new_entries)} new entries successfully added to the database.")

        invoice_data = generate_invoice(df)
        request.session["invoice_data"] = invoice_data
        request.session.modified = True  

        sheet_name_message = f"The sheet name is {sheet_name}. You can change it later."
        response_data = {
            "message": "File processed successfully!",
            "sheet_name": sheet_name_message if new_entries else "",
            "redirect_url": "/revenue_collection/list_projects/"
        }
        logger.info("File processing completed successfully.")
        return JsonResponse(response_data)

    except Exception as e:
        logger.critical(f"Unexpected processing error: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"Processing error: {str(e)}"}, status=400)


def generate_invoice(df):
    try:
        logger.info("Starting invoice generation process.")
        df['Start Time'] = pd.to_datetime(df['Start Time'], format='%H:%M', errors='coerce').dt.time
        df['End Time'] = pd.to_datetime(df['End Time'], format='%H:%M', errors='coerce').dt.time
        df = df.dropna(subset=['Start Time', 'End Time'])
        logger.info("Converted time fields successfully.")
        
        df['Hours Worked'] = df.apply(
            lambda row: (datetime.combine(datetime.min, row['End Time']) - 
                         datetime.combine(datetime.min, row['Start Time'])).seconds / 3600, axis=1)
        df['Cost'] = df['Hours Worked'] * df['Billable Rate']
        logger.info("Calculated billable hours and cost.")

        grouped = df.groupby(['Project', 'Employee ID']).agg(
            Total_Hours=('Hours Worked', 'sum'),
            Unit_Price=('Billable Rate', 'first'),
            Total_Cost=('Cost', 'sum')
        ).reset_index()

        invoice_data = {}
        for project, project_data in grouped.groupby('Project'):
            invoice_data[project] = project_data.to_dict(orient='records')

        logger.info("Invoice data successfully generated.")
        return invoice_data  

    except Exception as e:
        logger.error(f"Invoice generation error: {str(e)}", exc_info=True)
        return {"error": f"Invoice generation error: {str(e)}"}

    

@login_required(login_url='authentication:login')
def list_projects(request):
    logger.info(f"User {request.user} accessed the project list page.")
    invoice_data = request.session.get("invoice_data", {})
    
    if not invoice_data:
        logger.warning("No invoice data found in session for user %s.", request.user)
        return render(request, "bill_rate_system/view_invoice.html", {"invoice": "No invoice data found"})
    projects = list(invoice_data.keys())
    
    logger.info(f"Retrieved {len(projects)} projects from session data.")

    return render(request, "bill_rate_system/list_projects.html", {"projects": projects})


@login_required(login_url='authentication:login')
def view_invoice(request, project_name):
    logger.info(f"User {request.user} accessed invoice for project: {project_name}")
    invoice_data = request.session.get("invoice_data", {})

    if not invoice_data:
        logger.warning(f"No invoice data found in session for user {request.user}.")
        return render(request, "bill_rate_system/view_invoice.html", {
            "invoice": "No invoice data found",
            "error": "No invoice data found"
        })
    project_invoice = invoice_data.get(project_name)

    if not project_invoice:
        logger.warning(f"No invoice data found for project '{project_name}' requested by user {request.user}.")
        return render(request, "bill_rate_system/view_invoice.html", {
            "invoice": f"No data found for project: {project_name}",
            "error": f"No data found for project: {project_name}"
        })
    processed_invoice = []
    for entry in project_invoice:
        processed_invoice.append({
            "Employee_ID": entry["Employee ID"],
            "Total_Hours": entry["Total_Hours"],
            "Unit_Price": entry["Unit_Price"],
            "Total_Cost": entry["Total_Cost"]
        })
    logger.info(f"Successfully retrieved invoice data for project: {project_name}. Entries found: {len(processed_invoice)}")
    return render(request, "bill_rate_system/view_invoice.html", {
        "project": project_name,
        "invoice": processed_invoice
    })
    


@login_required(login_url='authentication:login')
def project_list(request):
    logger.info(f"User {request.user} accessed the project list.")
    projects = Project.objects.all()
    logger.info(f"Retrieved {projects.count()} projects from the database.")
    return render(request, 'bill_rate_system/project_list.html', {'projects': projects})

@login_required(login_url='authentication:login')
def timesheets(request):
    logger.info(f"User {request.user} accessed the timesheets page.")
    sheet_names = Timesheet.objects.values('sheet_name').distinct()
    timesheet_data = {sheet['sheet_name']: Timesheet.objects.filter(sheet_name=sheet['sheet_name']) for sheet in sheet_names}
    logger.info(f"Retrieved {len(timesheet_data)} distinct timesheets.")
    return render(request, 'bill_rate_system/timesheets.html', {'timesheet_data': timesheet_data})

@login_required(login_url='authentication:login')
def edit_timesheet_name(request, timesheet_id):
    timesheet = get_object_or_404(Timesheet, id=timesheet_id)
    timesheets = Timesheet.objects.filter(sheet_name=timesheet.sheet_name)
    logger.info(f"User {request.user} accessed timesheet edit page for ID {timesheet_id}.")

    if request.method == "POST":
        new_name = request.POST.get("sheet_name")
        if new_name:
            timesheets.update(sheet_name=new_name)
            logger.info(f"Updated timesheet name from {timesheet.sheet_name} to {new_name}.")
            messages.success(request, "All timesheets with this name have been updated successfully!")
            return render(request, "bill_rate_system/edit_timesheet.html", {"timesheet": timesheet})  
        else:
            logger.warning(f"User {request.user} attempted to rename a timesheet but provided an empty name.")
            messages.error(request, "Timesheet name cannot be empty.")

    return render(request, "bill_rate_system/edit_timesheet.html", {"timesheet": timesheet})

@login_required(login_url='authentication:login')
def timesheet_detail(request, sheet_name):
    logger.info(f"User {request.user} accessed timesheet details for sheet name {sheet_name}.")
    timesheets = Timesheet.objects.filter(sheet_name=sheet_name)
    logger.info(f"Retrieved {timesheets.count()} entries for sheet name {sheet_name}.")
    return render(request, 'bill_rate_system/timesheet_detail.html', {'timesheets': timesheets, "sheet_name": sheet_name})

@login_required(login_url='authentication:login')
def project_add(request):
    if request.method == 'POST':
        project_name = request.POST.get('firstname')
        if project_name:
            try:
                Project.objects.create(name=project_name)
                logger.info(f"User {request.user} added a new project: {project_name}.")
                messages.success(request, "Project added successfully!")
                return redirect('bill_rate_system:project_list')  
            except IntegrityError:
                logger.warning(f"User {request.user} attempted to add a duplicate project: {project_name}.")
                messages.error(request, "A project with this name already exists. Please choose a different name.")

    return render(request, 'bill_rate_system/project_add.html')


@login_required(login_url='authentication:login')
def project_edit(request, id):
    project = get_object_or_404(Project, id=id)
    logger.info(f"User {request.user} accessed project edit page for project ID {id}.")

    if request.method == 'POST':
        project_name = request.POST.get('firstname')
        if project_name:
            project.name = project_name
            project.save()
            logger.info(f"User {request.user} updated project ID {id} to new name {project_name}.")
            messages.success(request, "Project updated successfully!")
            return redirect('bill_rate_system:project_edit', id=id) 

    return render(request, 'bill_rate_system/project_edit.html', {'project': project})
