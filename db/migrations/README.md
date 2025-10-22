# Database Migrations

This directory will contain Alembic migration files.

To initialize Alembic:
```bash
alembic init alembic
```

To create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

To apply migrations:
```bash
alembic upgrade head
```
