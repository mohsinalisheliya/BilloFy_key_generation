# Key Generation System

A Django-based license key management system that generates and manages time-based license keys for clients using hardware ID verification.

## Features

- **License Key Generation**: Generate secure license keys based on hardware IDs with customizable validity periods
- **Client Management**: Track and manage client licenses with real-time status monitoring
- **Dashboard Interface**: User-friendly dashboard to view all clients, their license status, and remaining time
- **Search Functionality**: Quickly find clients by name or hardware ID
- **Authentication**: Secure login system to protect license management
- **Expiry Tracking**: Automatic tracking of license expiration with visual indicators for active/expired licenses
- **Time Display**: Shows remaining time in days, hours, or minutes for active licenses

## Tech Stack

- **Backend**: Django (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Django's built-in authentication system

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/key_generation.git
cd key_generation
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install django
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

7. Access the application at `http://127.0.0.1:8000/`

## Usage

1. Log in with your admin credentials
2. Use the dashboard to generate new license keys by providing:
   - Client name
   - Hardware ID
   - Validity duration (in seconds)
3. View all clients and their license status
4. Search for specific clients
5. Delete expired or invalid licenses

## License

This project is open source and available for use and modification.
