# API server

## DB
This project uses [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database migrations. See the [official documentation](https://alembic.sqlalchemy.org/en/latest/tutorial.html) for more information, including details about the structure of the related `alembic` folder and `alembic.ini`.

### Create tables
To create the tables in the database, run the following command:
```bash
alembic upgrade head
```

### Create a new migration
To create a new migration, run the following command:
```bash
alembic revision --autogenerate -m "migration message"
```