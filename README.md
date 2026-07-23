# MovieRec — AI-Powered Movie Recommendation System

## Overview
MovieRec is a complete Level 3 Movie Recommendation System built with Python, Flask, Pandas, Scikit-learn, and SQLite. It uses TF-IDF Vectorization and Cosine Similarity to recommend movies based on genres, cast, director, plot, and keywords. It includes user authentication, favorites, watchlists, recommendation history, and an admin dashboard.

## Tech Stack
- **Backend:** Python, Flask
- **Database:** SQLite (Flask-SQLAlchemy)
- **ML:** Pandas, NumPy, Scikit-learn, TF-IDF Vectorizer, Cosine Similarity
- **Frontend:** HTML, CSS (custom + Bootstrap 5), JavaScript
- **APIs:** TMDB (posters, ratings)

## Features

### User Features
- Search movies by title
- View detailed movie pages with posters, ratings, genres, director, cast
- Get top 10 similar movie recommendations
- Add/remove favorites and watchlist
- View recommendation history
- User login and registration

### Admin Features
- Login required (is_admin flag)
- Add new movies
- Delete movies
- Manage users and promote to admin
- Analytics: total users, favorites, watchlist items

### ML Pipeline
- Data cleaning with Pandas
- Combined feature vector (genres + overview + cast + director + keywords)
- TF-IDF Vectorization
- Cosine Similarity matrix
- Top-N recommendations

## Folder Structure
```
MovieRecommendation/
├── app.py                 # Flask application
├── recommendation.py       # ML engine (TF-IDF + Cosine)
├── models.py               # Database models
├── movies.csv              # Movie dataset
├── model.pkl               # Serialized similarity model
├── database.db             # SQLite database
├── requirements.txt
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   └── images/poster_placeholder.jpg
└── templates/
    ├── base.html
    ├── index.html
    ├── results.html
    ├── movie.html
    ├── recommendations.html
    ├── login.html
    ├── profile.html
    └── admin.html
```

## Installation

```bash
pip install -r requirements.txt
python app.py
```

The app will run at `http://localhost:5000`.

## Usage
1. Open `http://localhost:5000`
2. Search for a movie (e.g., "Inception")
3. Click a movie to see details and recommendations
4. Register/login to save favorites and build your watchlist
5. Visit `/profile` to see your favorites, watchlist, and recommendation history
6. Create an admin user and visit `/admin` for dashboard features

## Dataset
A synthetic dataset of 38 popular movies is included in `movies.csv`. It contains:
- Title, Genres, Overview, Cast, Director, Rating, Year, Keywords

The dataset was chosen to cover diverse genres and well-known films for demonstration.

## Advanced Features Implemented
- Personalized recommendation history tracking per user
- Dark cinematic theme with glassmorphism cards
- Responsive Bootstrap layout
- Search suggestions through live filtering
- Movie posters via TMDB API (falls back to custom placeholder)
- Admin analytics dashboard

## Resume Description
**Movie Recommendation System:** Developed a machine learning-based recommendation engine using Python, Pandas, Scikit-learn, TF-IDF Vectorization, and Cosine Similarity. Built a responsive web application with Flask that recommends similar movies, displays posters and details using TMDB APIs, and supports personalized favorites, watchlists, recommendation history, user authentication, and an admin dashboard with analytics.
