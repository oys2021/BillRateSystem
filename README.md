# Revenue Collection & Bill Rate  System

## Introduction
The **Timesheet & Invoice Management System** is a Django-based web application designed to facilitate efficient timesheet management, invoice generation, and company/project tracking. It allows finance team to upload timesheets, validate records and generate invoices.

## Features
- **Timesheet Upload & Validation**: Bulk upload of timesheets with  validation.
- **Invoice Generation**:  Invoice creation based on timesheet data(Company).
- **Timesheet Management**: Track timesheet and their associated projects/companies.
- **Logging & Error Handling**: Robust logging mechanisms for debugging.
- **Test**: Robust tests for debugging.


## Technologies

- **Backend**: Django and whienoise for serving the static files
- **Frontend**: Html,Css,Javascript
- **Database**: Sqlite3 (or your preferred database)
- **Test**:Pytest for tests.


## Installation

### Prerequisites
Ensure you have the following installed:
- Python 3.8+
- Pip
- Django 4+
- PostgreSQL (or SQLite for development) or any prefered database.
- Virtual environment (recommended)

### Setup
1. **Clone the Repository**
   ```sh
   git clone https://github.com/oys2021/BillRateSystem.git
   cd BillRateSystem

2. **Create and Activate a Virtual Environment**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate


3. **Install Dependencies**
   ```sh
   pip install -r requirements.txt

4. **Configure Environment Variables**
    ```sh
    create a .env or environment variable and have 
    DEBUG=False
    SECRET_KEY=your_secret_key_here
    Setup prefered DB and add the configuration key in the .env 

5. **Add the ALLOWED_HOSTS setting**
    ```sh
    If you’re deploying the app, replace it with the actual domain(Optioanl):
    ALLOWED_HOSTS = ["yourdomain.com", "www.yourdomain.com"]


6. **Run Migrations**
    ```sh
    python manage.py migrate

7. **Run the Server**
    ```sh
    python manage.py runserver


## Usage

- **Login**: Users(Finance Team) can log in by providing a username and password. 

- **Add Company or Project**: After login, users(Finance team) can add project/company to system.All projects in the timesheet that are not registered in the system are rejected and an error is thrown.
  
- **Upload Timesheet**: After login, users(Finance team) can upload a valid and cleaned timesheet in csv format only and view generated invoices.
  
- **View Stored Timesheets**: Users can view timesheets previously uploaded , view them, and group them by day, week, or month.



