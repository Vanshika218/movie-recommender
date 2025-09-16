from flask import Flask, render_template, request
from collections import defaultdict
import os
import pandas as pd
import json
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

app = Flask(__name__)

# Load and prepare data
df = pd.read_csv('tmdb_5000_movies_subset.csv').head(1000)  # Limit to 1000 rows
credits_df = pd.read_csv('tmdb_5000_credits_subset.csv').head(1000)

# Merge on movie ID
df = movies_df.merge(credits_df, left_on='id', right_on='movie_id', how='inner')
df = df.drop(columns=['movie_id', 'title_y']).rename(columns={'title_x': 'title'})

# Extract director from crew
def get_director(x):
    try:
        crew = json.loads(x)
        for i in crew:
            if i['job'] == 'Director':
                return i['name']
        return ''
    except:
        return ''

df['director'] = df['crew'].apply(get_director)

# Extract top 3 cast
def get_top_cast(x, n=3):
    try:
        cast = json.loads(x)
        return [i['name'] for i in cast[:n]]
    except:
        return []

df['top_cast'] = df['cast'].apply(get_top_cast)

# Extract lists from JSON strings
def get_list(x):
    try:
        items = json.loads(x)
        return [i['name'] for i in items]
    except:
        return []

df['genres_list'] = df['genres'].apply(get_list)
df['keywords_list'] = df['keywords'].apply(get_list)

# Create feature soup for similarity
def create_soup(x):
    overview = str(x['overview']) if pd.notnull(x['overview']) else ''
    return ' '.join(x['genres_list']) + ' ' + ' '.join(x['keywords_list']) + ' ' + overview + ' ' + x['director'] + ' ' + ' '.join(x['top_cast'])

df['soup'] = df.apply(create_soup, axis=1)

# TF-IDF and cosine similarity
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(df['soup'])
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

# Title to index mapping
indices = pd.Series(df.index, index=df['title']).drop_duplicates()

# Get similar movies
def get_recommendations(title, n=50):
    if title not in indices:
        return []
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:n+1]  # Exclude self
    movie_indices = [i[0] for i in sim_scores]
    return df['title'].iloc[movie_indices]

# Get movie details from DataFrame and TMDB API
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "6cf8c75b96fccf52ba6b8c310aafe1d3")
def get_movie_details(title):
    if title not in df['title'].values:
        return "No description found.", "https://via.placeholder.com/300x200?text=No+Poster", "Unknown"
    movie = df[df['title'] == title].iloc[0]
    summary = movie['overview'] if pd.notnull(movie['overview']) else "No description available."
    genre_text = ", ".join(movie['genres_list']) if movie['genres_list'] else "Unknown"
    try:
        query = title
        url = "https://api.themoviedb.org/3/search/movie"
        params = {"api_key": TMDB_API_KEY, "query": query}
        response = requests.get(url, params=params)
        data = response.json()
        if data["results"]:
            poster_path = data["results"][0].get("poster_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://via.placeholder.com/300x200?text=No+Poster"
        else:
            poster_url = "https://via.placeholder.com/300x200?text=No+Poster"
    except Exception as e:
        print(f"TMDB API error for {title}: {e}")  # Debug
        poster_url = "https://via.placeholder.com/300x200?text=Error"
    return summary, poster_url, genre_text

@app.route("/", methods=["GET", "POST"])
def home():
    recommendations = []
    if request.method == "POST":
        movie_title = request.form.get("movie_title")
        selected_genre = request.form.get("genre")
        print(f"Received movie_title: {movie_title}, genre: {selected_genre}")  # Debug
        if movie_title:
            similar_titles = get_recommendations(movie_title, n=50)
            print(f"Similar titles: {similar_titles.tolist()}")  # Debug
            count = 0
            for sim_title in similar_titles:
                if count >= 5:
                    break
                summary, poster, genre_text = get_movie_details(sim_title)
                if selected_genre and selected_genre.lower() not in genre_text.lower():
                    continue
                rating = df[df['title'] == sim_title]['vote_average'].iloc[0] if pd.notnull(df[df['title'] == sim_title]['vote_average'].iloc[0]) else "N/A"
                recommendations.append((sim_title, rating, summary, poster, genre_text))
                count += 1
    return render_template("index.html", recommendations=recommendations)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Use Render's PORT or default to 10000
    app.run(host="0.0.0.0", port=port, debug=True)