FROM python:3.10-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Pre-download the MovieLens dataset to avoid runtime download
RUN python -c "from surprise import Dataset; Dataset.load_builtin('ml-100k')"

# Copy your Flask app
COPY . .

# Expose port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
