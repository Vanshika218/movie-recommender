# Pre-download MovieLens 100k dataset
RUN mkdir -p ~/.surprise_data/ml-100k/ml-100k && \
    wget -q -O ~/.surprise_data/ml-100k/ml-100k/u.data https://files.grouplens.org/datasets/movielens/ml-100k/u.data && \
    wget -q -O ~/.surprise_data/ml-100k/ml-100k/u.item https://files.grouplens.org/datasets/movielens/ml-100k/u.item && \
    wget -q -O ~/.surprise_data/ml-100k/ml-100k/u.user https://files.grouplens.org/datasets/movielens/ml-100k/u.user && \
    wget -q -O ~/.surprise_data/ml-100k/ml-100k/u.genre https://files.grouplens.org/datasets/movielens/ml-100k/u.genre

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
