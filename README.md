# Timesheet & Invoice Management System

## Introduction
The **Timesheet & Invoice Management System** is a Django-based web application designed to facilitate efficient timesheet management, invoice generation, and company/project tracking. It allows finance team to upload timesheets, validate records, generate invoices, and manage projects/companies effectively.

## Features
- **Timesheet Upload & Validation**: Bulk upload of timesheets with automated validation.
- **Invoice Generation**: Automated invoice creation based on timesheet data.
- **Project Management**: Track projects and their associated timesheets.
- **Database Queries Optimization**: Efficient querying for improved performance.
- **Logging & Error Handling**: Robust logging mechanisms for debugging.

## Installation

### Prerequisites
Ensure you have the following installed:
- Python 3.8+
- Django 4+
- PostgreSQL (or SQLite for development)
- Virtual environment (optional but recommended)

### Setup
1. **Clone the Repository**
   ```sh
   git clone https://github.com/oys2021/BillRateSystem.git
   cd timesheet-invoice

2. **Create and Activate a Virtual Environment**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate


3. **Install Dependencies**
   ```sh
   pip install -r requirements.txt

4. **Configure Environment Variables**
    DEBUG=True
    SECRET_KEY=your_secret_key_here

5. **Run Migrations**
    python manage.py migrate

6. **Run the Server**
    python manage.py runserver





