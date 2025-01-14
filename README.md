# BounceBack Project

## Overview

BounceBack is a shift management system designed to help administrators manage shifts and workers efficiently. The system includes features such as shift creation, reporting, notifications, and more.

## Features

- Admin dashboard for managing shifts and users
- Worker dashboard for viewing and signing off shifts
- Reporting functionality with export to Excel
- Notifications via SMS using Twilio
- DataTables integration for enhanced table functionalities
- Select2 integration for improved user selection

## Technologies Used

- Django
- PostgreSQL (Or any database of choice)
- Firebase (for SMS notifications)
- DataTables
- Select2
- Bootstrap

## Setup Instructions

### Prerequisites

- Python 3.x
- PostgreSQL
- firebase account (for SMS notifications)
- Heroku account (optional for deployment)

### Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/bounceback.git
    cd bounceback
    ```

2. **Create a virtual environment:**

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4. **Set up the database:**

    Create a PostgreSQL database and update the `DATABASES` setting in `settings.py` with your database credentials.

5. **Run migrations:**

    ```sh
    python manage.py migrate
    ```

6. **Create a superuser:**

    ```sh
    python manage.py createsuperuser
    ```

7. **Run the development server:**

    ```sh
    python manage.py runserver
    ```

### Environment Variables

Create a [.env](http://_vscodecontentref_/1) file in the project root and add the following environment variables:

```env```
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=your_database_url
FCM_API_KEY: "[your api key]",
GCM_API_KEY: "[your api key]",
APNS_CERTIFICATE: "/path/to/your/certificate.pem",

## Usage

### Admin Dashboard

Manage Shifts: Create, edit, and delete shifts.
Manage Users: Create, edit, and delete users.
Reporting: Generate reports and export to Excel.
Notifications: Send SMS notifications to users.
Timesheet Generation on a weekly basis and download to pdf
Manage Locations: Create, edit, and delete locations.
View Availability of users.

### Worker Dashboard

View Shifts: View today's shifts, upcoming shifts, and previous shifts.
Sign Off Shifts: Sign off completed shifts.
Set Availability.

## Contributing

Fork the repository.
Create a new branch (git checkout -b feature-branch).
Make your changes.
Commit your changes (git commit -m 'Add some feature').
Push to the branch (git push origin feature-branch).
Open a pull request.

## Contact

For any inquiries, please contact [mail to](samuel.eabs@gmail.com)

License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

[Django](https://www.djangoproject.com/)
[Firebase](https://firebase.google.com/)
[DataTables](https://datatables.net/)
[Select2](https://select2.org/)
[Bootstrap](https://getbootstrap.com/)