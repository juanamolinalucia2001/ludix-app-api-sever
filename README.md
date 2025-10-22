# Ludix App AI Server

A FastAPI backend for the Ludix educational quiz application, implementing modern design patterns and best practices.

## Stack

- **Framework**: Python FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Authentication**: JWT (JSON Web Tokens) with OAuth2
- **Containerization**: Docker

## Design Patterns

This project implements three key design patterns:

1. **Factory Pattern**: Database session creation (`db/base.py`)
   - `SessionLocal` factory creates new database sessions for each request
   - `get_db()` dependency function manages session lifecycle

2. **Observer Pattern**: Progress tracking (`models/`)
   - User quiz progress can be tracked through quiz attempts
   - Future implementation for real-time progress notifications

3. **Decorator Pattern**: Authentication (`services/AuthService.py`)
   - JWT token-based authentication decorates protected endpoints
   - Layered authentication checks (token validation, active user status)

## Project Structure

```
ludix-app-ai-sever/
├── db/
│   ├── base.py              # Database configuration and session factory
│   └── migrations/          # Alembic migration files (placeholder)
├── models/
│   ├── User.py              # User SQLAlchemy model
│   └── Quiz.py              # Quiz SQLAlchemy model
├── services/
│   └── AuthService.py       # Authentication service with decorator pattern
├── routers/
│   └── auth.py              # Authentication endpoints
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker container configuration
└── README.md               # This file
```

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL (optional, defaults to PostgreSQL but can use SQLite for development)
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/juanamolinalucia2001/ludix-app-ai-sever.git
cd ludix-app-ai-sever
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/ludix_db"
export SECRET_KEY="your-secret-key-change-in-production"
```

For development with SQLite:
```bash
export DATABASE_URL="sqlite:///./ludix.db"
```

### Running the Application

#### Development Server

```bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

#### Using Docker

```bash
# Build the image
docker build -t ludix-app-ai-server .

# Run the container
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:password@host:5432/ludix_db" \
  -e SECRET_KEY="your-secret-key" \
  ludix-app-ai-server
```

## API Endpoints

### Root Endpoints

- `GET /` - API health check and information
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### Authentication Endpoints

- `POST /auth/register` - Register a new user
  - Body: `{ "username": "string", "email": "string", "password": "string", "full_name": "string" }`
  - Returns: User information

- `POST /auth/login` - Login to get access token
  - Body (form-data): `username=string&password=string`
  - Returns: `{ "access_token": "string", "token_type": "bearer" }`

- `GET /auth/me` - Get current authenticated user
  - Header: `Authorization: Bearer <token>`
  - Returns: User information

## Database Models

### User Model

- `id`: Integer, primary key
- `username`: String(50), unique, indexed
- `email`: String(100), unique, indexed
- `hashed_password`: String(255)
- `full_name`: String(100), optional
- `is_active`: Boolean, default True
- `is_admin`: Boolean, default False
- `created_at`: DateTime
- `updated_at`: DateTime

### Quiz Model

- `id`: Integer, primary key
- `title`: String(200)
- `description`: Text, optional
- `difficulty_level`: String(20), default "beginner"
- `category`: String(50), optional
- `is_active`: Boolean, default True
- `created_by`: Foreign key to User
- `created_at`: DateTime
- `updated_at`: DateTime

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://ludix_user:ludix_password@localhost:5432/ludix_db` |
| `SECRET_KEY` | JWT secret key for token signing | `your-secret-key-change-in-production` |

⚠️ **Important**: Always change the `SECRET_KEY` in production!

## Database Migrations

This project uses Alembic for database migrations.

### Initialize Alembic (if needed)

```bash
alembic init alembic
```

### Create a migration

```bash
alembic revision --autogenerate -m "description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback migrations

```bash
alembic downgrade -1
```

## Security

- Passwords are hashed using bcrypt
- JWT tokens expire after 30 minutes
- All authentication endpoints use industry-standard OAuth2 flows
- Dependencies are checked for known vulnerabilities

## Development

### Running Tests

```bash
# Coming soon
pytest
```

### Code Style

```bash
# Format code
black .

# Lint code
flake8 .
```

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
