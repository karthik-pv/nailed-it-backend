# NailedIt Quote AI - Backend

A robust Flask backend for the NailedIt Quote AI application with comprehensive user and company onboarding functionality.

## Features

- 🔐 **Secure Authentication** - Supabase Auth integration with JWT tokens
- 🏢 **Company Management** - Full CRUD operations for companies
- 👥 **User Management** - User profiles and company associations
- 📁 **File Storage** - Supabase Storage for logos and documents
- 🔒 **Row Level Security** - Comprehensive RLS policies
- 🛡️ **Input Validation** - Robust validation and error handling
- 📊 **Logging** - Comprehensive logging for debugging and monitoring

## Project Structure

```
backend/
├── sql/                    # Database setup scripts
│   ├── 01_setup_tables.sql
│   ├── 02_setup_triggers.sql
│   ├── 03_setup_rls_policies.sql
│   └── README.md
├── auth.py                 # Authentication service
├── storage.py             # File storage service
├── companies.py           # Company CRUD operations
├── users.py               # User CRUD operations
├── server.py              # Main Flask application
├── supabase_client.py     # Supabase client setup
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
└── README.md             # This file
```

## Prerequisites

1. **Python 3.8+** installed
2. **Supabase Project** set up
3. **Environment Variables** configured

## Setup Instructions

### 1. Environment Setup

Create a `.env` file in the backend directory:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
FLASK_ENV=development
PORT=5000
```

### 2. Database Setup

1. **Run SQL Scripts** in Supabase SQL Editor (in order):

   ```sql
   -- 1. Create tables and indexes
   -- Run: sql/01_setup_tables.sql

   -- 2. Create triggers and functions
   -- Run: sql/02_setup_triggers.sql

   -- 3. Setup RLS policies
   -- Run: sql/03_setup_rls_policies.sql
   ```

2. **Verify Setup**:
   - Check tables exist: `users`, `companies`
   - Check storage bucket exists: `company-assets`
   - Verify RLS is enabled on both tables

### 3. Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run the Application

```bash
# Development mode
python server.py

# Production mode (using gunicorn)
gunicorn --bind 0.0.0.0:5000 server:app
```

## API Endpoints

### Authentication

- `POST /auth/signup` - Register new user
- `POST /auth/signin` - Sign in user
- `POST /auth/signout` - Sign out user
- `GET /auth/user` - Get current user profile

### Companies

- `POST /companies` - Create company
- `GET /companies/<id>` - Get company details
- `PUT /companies/<id>` - Update company
- `DELETE /companies/<id>` - Delete company
- `GET /companies/<id>/users` - Get company users
- `POST /companies/<id>/logo` - Upload company logo
- `POST /companies/<id>/pricing-document` - Upload pricing document
- `POST /companies/join` - Join existing company

### Users

- `GET /users/<id>` - Get user details
- `PUT /users/<id>` - Update user
- `POST /users/<id>/leave-company` - Leave company

### Onboarding

- `POST /onboarding/complete` - Complete onboarding process

### File Uploads

- `POST /upload/logo` - Upload logo file
- `POST /upload/document` - Upload document file

### Utility

- `GET /health` - Health check endpoint

## Authentication

All protected endpoints require a Bearer token:

```bash
# Header format
Authorization: Bearer <supabase_jwt_token>
```

## Request/Response Examples

### User Registration

```bash
curl -X POST http://localhost:5000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'
```

### Company Creation

```bash
curl -X POST http://localhost:5000/companies \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "company_name": "My Fencing Company",
    "owner_name": "John Doe",
    "email": "contact@fencing.com",
    "phone": "+1-555-123-4567",
    "website": "https://fencing.com",
    "description": "Professional fencing services"
  }'
```

### File Upload

```bash
curl -X POST http://localhost:5000/upload/logo \
  -H "Authorization: Bearer <token>" \
  -F "file=@logo.png"
```

## Security Features

### Row Level Security (RLS)

- Users can only access their own data
- Company members can view other company members
- Proper authorization checks on all operations

### Input Validation

- Required field validation
- File type and size validation
- Email format validation
- Unique constraint validation

### Error Handling

- Comprehensive error messages
- Proper HTTP status codes
- Security-safe error responses

## File Storage

### Organization

Files are stored in Supabase Storage with the following structure:

```
company-assets/
├── {user_id}/
│   ├── logo/
│   │   └── {unique_filename}.{ext}
│   └── document/
│       └── {unique_filename}.{ext}
```

### Supported File Types

**Logos**: JPG, PNG, GIF, WebP (max 5MB)
**Documents**: PDF, DOC, DOCX, XLS, XLSX, TXT, CSV (max 10MB)

## Logging

The application uses Python's logging module:

- **INFO**: Successful operations
- **WARNING**: Non-critical issues
- **ERROR**: Error conditions
- **DEBUG**: Detailed debugging information

## Development

### Adding New Features

1. **Add Business Logic**: Create/update service modules
2. **Add Routes**: Update `server.py` with new endpoints
3. **Update Database**: Add migrations if needed
4. **Add Tests**: Create test cases for new functionality

### Code Organization

- **Services**: Business logic separated into modules
- **Authentication**: Centralized auth middleware
- **Validation**: Input validation in service layers
- **Error Handling**: Consistent error responses

## Production Deployment

### Environment Variables

Ensure all environment variables are set:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`
- `FLASK_ENV=production`
- `PORT=5000`

### Using Gunicorn

```bash
# Basic production setup
gunicorn --bind 0.0.0.0:5000 --workers 4 server:app

# With SSL and advanced options
gunicorn --bind 0.0.0.0:443 --workers 4 --timeout 120 \
  --keyfile=key.pem --certfile=cert.pem server:app
```

## Troubleshooting

### Common Issues

**1. Database Connection Issues**

- Verify Supabase URL and keys
- Check network connectivity
- Ensure RLS policies are correctly set

**2. Authentication Failures**

- Verify JWT secret configuration
- Check token expiration
- Ensure proper Authorization header format

**3. File Upload Issues**

- Check file size limits
- Verify storage bucket permissions
- Ensure proper content-type headers

**4. CORS Issues**

- Update CORS origins in `server.py`
- Check preflight request handling

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues and questions:

1. Check the logs for error messages
2. Verify database setup using SQL scripts
3. Test endpoints using the health check
4. Review Supabase dashboard for errors

## License

This project is part of the NailedIt Quote AI application.
