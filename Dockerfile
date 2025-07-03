# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app

# Install system dependencies needed for mysqlclient build
RUN apt-get update && apt-get install -y \
    pkg-config \
    build-essential \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY . /app/

# Expose the port the app runs on
EXPOSE 8001

# Define the command to run your app, pointing to the correct WSGI module
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "PlatformInterview.wsgi:application"]
