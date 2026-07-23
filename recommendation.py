import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

MODEL_FILE = os.path.join(os.path.dirname(__file__), 'model.pkl')

def build_model():
    csv_path = os.path.join(os.path.dirname(__file__), 'movies.csv')
    df = pd.read_csv(csv_path)
    # Fill NA
    df['genres'] = df['genres'].fillna('')
    df['overview'] = df['overview'].fillna('')
    df['cast'] = df['cast'].fillna('')
    df['director'] = df['director'].fillna('')
    df['keywords'] = df['keywords'].fillna('')
    df['rating'] = df['rating'].fillna(5.0)

    # Combine features
    df['combined_features'] = (
        df['genres'] + ' ' +
        df['overview'] + ' ' +
        df['cast'] + ' ' +
        df['director'] + ' ' +
        df['keywords']
    )
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['combined_features'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    indices = pd.Series(df.index, index=df['title']).drop_duplicates()

    with open(MODEL_FILE, 'wb') as f:
        pickle.dump({'cosine_sim': cosine_sim, 'indices': indices, 'df': df}, f)
    print("Model rebuilt and saved to", MODEL_FILE)

def recommend_movies(title, top_n=10):
    if not os.path.exists(MODEL_FILE):
        build_model()
    with open(MODEL_FILE, 'rb') as f:
        data = pickle.load(f)
    cosine_sim = data['cosine_sim']
    indices = data['indices']
    df = data['df']

    if title not in indices:
        # Partial match
        matches = df[df['title'].str.contains(title, case=False, na=False)]
        if matches.empty:
            return []
        title = matches.iloc[0]['title']
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:top_n+1]
    movie_indices = [i[0] for i in sim_scores]
    recommendations = df.iloc[movie_indices][['title', 'genres', 'rating', 'year', 'overview', 'director', 'cast']].to_dict('records')
    return recommendations

# Build model on import if needed
if not os.path.exists(MODEL_FILE):
    build_model()
