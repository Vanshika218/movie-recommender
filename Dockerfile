# Use Python 3.10 (works with scikit-surprise)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for scikit-surprise
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of your project
COPY . .

# Start the Flask app with gunicorn
CMD ["gunicorn", "app:app"]
