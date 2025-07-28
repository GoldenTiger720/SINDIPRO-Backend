# SINDIPRO Backend

Django REST API backend for the SINDIPRO condominium management system.

## Features

- **Authentication**: JWT-based authentication with role-based access control
- **Building Management**: Comprehensive building and unit registry
- **Legal Documents**: Document management and legal obligations tracking
- **Equipment Management**: Equipment inventory and maintenance tracking
- **Financial Management**: Budget tracking and expense management
- **Consumption Tracking**: Utility consumption monitoring (water, electricity, gas)
- **Field Management**: Request management and surveys
- **Reporting**: Generate and schedule various reports
- **User Management**: Role-based user access control

## Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Virtual Environment

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd SINDIPRO-backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup:**
   - Create a PostgreSQL database named `sindipro_db`
   - Create a PostgreSQL user `sindipro_user` with password
   - Grant all privileges on the database to the user

5. **Environment Configuration:**
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your database credentials and settings.

6. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

7. **Create Superuser:**
   ```bash
   python manage.py createsuperuser
   ```

8. **Start Development Server:**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/`

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Login (get JWT tokens)
- `POST /api/auth/refresh/` - Refresh JWT token
- `POST /api/auth/register/` - Register new user
- `GET/PUT /api/auth/profile/` - User profile

### Buildings
- `GET/POST /api/buildings/` - List/Create buildings
- `GET/PUT/DELETE /api/buildings/{id}/` - Building details
- `GET/POST /api/buildings/{id}/units/` - Building units

### Legal Documents
- `GET/POST /api/legal/documents/` - Legal documents
- `GET/POST /api/legal/obligations/` - Legal obligations

### Equipment
- `GET/POST /api/equipment/` - Equipment list
- `GET/POST /api/equipment/{id}/maintenance/` - Maintenance records

### Financial
- `GET/POST /api/financial/budgets/` - Budget management
- `GET/POST /api/financial/expenses/` - Expense tracking
- `GET/POST /api/financial/revenues/` - Revenue tracking

### Consumption
- `GET/POST /api/consumption/readings/` - Consumption readings
- `GET /api/consumption/types/` - Consumption types

### Field Management
- `GET/POST /api/field/requests/` - Field requests
- `GET/POST /api/field/surveys/` - Surveys

### Reports
- `GET/POST /api/reports/templates/` - Report templates
- `GET/POST /api/reports/generate/` - Generate reports

### User Management
- `GET/POST /api/users/` - User management
- `GET/PUT /api/users/{id}/access/` - Building access management

## User Roles

- **Master**: Full access to all modules and system settings
- **Manager**: Admin access except critical system settings
- **Field**: Limited access to field requests and consumption only
- **Read-Only**: View-only access to assigned modules

## Database Models

The system includes comprehensive models for:
- User management with custom user model
- Building and unit registry
- Legal document and obligation tracking
- Equipment and maintenance management
- Financial budget and expense tracking
- Utility consumption monitoring
- Field request and survey management
- Report generation and scheduling
- Activity logging and access control

## Development

To add new features:
1. Create/modify models in the appropriate app
2. Create/update serializers
3. Create/update views
4. Add URL patterns
5. Run migrations
6. Update tests

## Security

- JWT-based authentication
- Role-based access control
- CORS configuration for frontend integration
- File upload security
- Database connection security

## License

This project is proprietary software for SINDIPRO.