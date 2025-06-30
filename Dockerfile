# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY . /app/

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run your app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "Netrika.wsgi:application"]