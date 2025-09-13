# Use Python 3.10 slim as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install build dependencies and wget
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Pre-download MovieLens 100k dataset
RUN mkdir -p /root/.surprise_data/ml-100k/ml-100k && \
    wget -q -O /root/.surprise_data/ml-100k/ml-100k/u.data https://files.grouplens.org/datasets/movielens/ml-100k/u.data && \
    wget -q -O /root/.surprise_data/ml-100k/ml-100k/u.item https://files.grouplens.org/datasets/movielens/ml-100k/u.item && \
    wget -q -O /root/.surprise_data/ml-100k/ml-100k/u.user https://files.grouplens.org/datasets/movielens/ml-100k/u.user && \
    wget -q -O /root/.surprise_data/ml-100k/ml-100k/u.genre https://files.grouplens.org/datasets/movielens/ml-100k/u.genre

# Copy the rest of the project
COPY . .

# Expose Flask port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
