from flask import Flask, render_template, request
from surprise import SVD, Dataset
from surprise.model_selection import train_test_split
from collections import defaultdict
import random
import os
import requests
import re

app = Flask(__name__)

# TMDb API key
TMDB_API_KEY = "6cf8c75b96fccf52ba6b8c310aafe1d3"

# Function to clean MovieLens titles before searching TMDb
def clean_title(title):
    # Remove year in parentheses e.g. "(1996)"
    title = re.sub(r"\(\d{4}\)", "", title).strip()

    # Handle cases like "Usual Suspects, The" → "The Usual Suspects"
    if ", The" in title:
        title = "The " + title.replace(", The", "")
    elif ", An" in title:
        title = "An " + title.replace(", An", "")
    elif ", A" in title:
        title = "A " + title.replace(", A", "")

    return title.strip()

# Function to fetch movie details (poster + summary) from TMDb API
def get_movie_details(title):
    try:
        query = clean_title(title)

        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": query
        }
        response = requests.get(url, params=params)
        data = response.json()

        if data["results"]:
            movie = data["results"][0]
            summary = movie.get("overview", "No description available.")
            poster_path = movie.get("poster_path")
            poster_url = (
                f"https://image.tmdb.org/t/p/w500{poster_path}"
                if poster_path else "https://via.placeholder.com/300x200?text=No+Poster"
            )
            return summary, poster_url
        else:
            return "No description found.", "https://via.placeholder.com/300x200?text=No+Poster"
    except Exception:
        return "Error retrieving description.", "https://via.placeholder.com/300x200?text=Error"

# Load MovieLens data
data = Dataset.load_builtin('ml-100k')
trainset, testset = train_test_split(data, test_size=0.25)

algo = SVD()
algo.fit(trainset)

# Load movie names
movie_names = {}
path = os.path.expanduser("~/.surprise_data/ml-100k/ml-100k/u.item")
with open(path, encoding='ISO-8859-1') as f:
    for line in f:
        parts = line.strip().split('|')
        movie_id, movie_name = parts[0], parts[1]
        movie_names[movie_id] = movie_name

# Get top N predictions
def get_top_n(predictions, n=5):
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        top_n[uid].append((iid, est))
    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]
    return top_n

predictions = algo.test(testset)
top_n = get_top_n(predictions, n=5)

@app.route("/", methods=["GET", "POST"])
def home():
    recommendations = []
    if request.method == "POST":
        user_id = request.form.get("user_id")
        if user_id in top_n:
            for iid, rating in top_n[user_id]:
                name = movie_names[iid]
                summary, poster = get_movie_details(name)
                recommendations.append((name, rating, summary, poster))
        else:
            random_movies = random.sample(list(movie_names.items()), 5)
            for _, name in random_movies:
                summary, poster = get_movie_details(name)
                recommendations.append((name, None, summary, poster))
    return render_template("index.html", recommendations=recommendations)

if __name__ == "__main__":
    app.run(debug=True)
