# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set environment variables to prevent Python from writing .pyc files and enable buffer flushing
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (for psycopg2 and other libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Add a non-root user for security
RUN useradd -m flaskuser
USER flaskuser

# Expose the Flask application's default port
EXPOSE 5000

# Set environment variables for Flask (configurable at runtime)
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Default command to run the application
CMD ["flask", "run"]


