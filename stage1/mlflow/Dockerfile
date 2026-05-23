# Start from the official MLflow image
FROM ghcr.io/mlflow/mlflow:v2.11.1

# What this does: installs psycopg2-binary which is the PostgreSQL
# driver Python needs to connect to a PostgreSQL database.
# We use the 'binary' version because it has no system dependencies
# making it simpler to install in a container environment.
RUN pip install psycopg2-binary

# Expose the MLflow port
EXPOSE 5000
