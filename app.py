from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import numpy as np
import pickle
import os
import requests
from datetime import datetime

from extensions import db, login_manager
from models import User, Favorite, Watchlist, RecommendationHistory

app = Flask(__name__)
app.secret_key = 'movie-rec-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize database
with app.app_context():
    db.create_all()

# Import recommendation after everything is initialized
from recommendation import recommend_movies, build_model

TMDB_API_KEY = "your_tmdb_api_key"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper to fetch poster

def get_movie_poster(title, year=None):
    try:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
        if year:
            url += f"&year={year}"
        resp = requests.get(url, timeout=3)
        data = resp.json()
        if data.get('results'):
            poster_path = data['results'][0].get('poster_path')
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except Exception:
        pass
    return url_for('static', filename='images/poster_placeholder.jpg')

def get_movie_details(title):
    try:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
        resp = requests.get(url, timeout=3)
        data = resp.json()
        if data.get('results'):
            movie = data['results'][0]
            return {
                'rating': movie.get('vote_average', 'N/A'),
                'overview': movie.get('overview', ''),
                'release_date': movie.get('release_date', ''),
                'genres': [g['name'] for g in movie.get('genres', [])],
                'poster': f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get('poster_path') else None
            }
    except Exception:
        pass
    return None

@app.route('/')
def index():
    # Show some trending movies
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'movies.csv'))
    trending = df.sort_values('rating', ascending=False).head(8).to_dict('records')
    for movie in trending:
        movie['poster'] = get_movie_poster(movie['title'], movie.get('year'))
    return render_template('index.html', trending=trending)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('index'))
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'movies.csv'))
    matches = df[df['title'].str.contains(query, case=False, na=False)]
    movies = matches.head(10).to_dict('records')
    for movie in movies:
        movie['poster'] = get_movie_poster(movie['title'], movie.get('year'))
    return render_template('results.html', query=query, movies=movies)

@app.route('/movie/<title>')
def movie_details(title):
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'movies.csv'))
    movie_row = df[df['title'] == title]
    if movie_row.empty:
        movie_row = df[df['title'].str.contains(title, case=False, na=False)].head(1)
    if movie_row.empty:
        flash("Movie not found.", "danger")
        return redirect(url_for('index'))
    movie_info = movie_row.iloc[0].to_dict()
    recommendations = recommend_movies(title)
    for rec in recommendations:
        rec['poster'] = get_movie_poster(rec['title'], rec.get('year'))
    movie_info['poster'] = get_movie_poster(movie_info['title'], movie_info.get('year'))
    details = get_movie_details(title)
    if details:
        movie_info['tmdb_rating'] = details['rating']
        movie_info['tmdb_overview'] = details['overview']
    in_fav = False
    in_watch = False
    if current_user.is_authenticated:
        in_fav = Favorite.query.filter_by(user_id=current_user.id, movie_title=title).first() is not None
        in_watch = Watchlist.query.filter_by(user_id=current_user.id, movie_title=title).first() is not None
    # Log recommendation history
    if current_user.is_authenticated:
        history = RecommendationHistory.query.filter_by(user_id=current_user.id, movie_title=title).first()
        if not history:
            hist = RecommendationHistory(user_id=current_user.id, movie_title=title, recommended_for=title)
            db.session.add(hist)
            db.session.commit()
    return render_template('movie.html', movie=movie_info, recommendations=recommendations, in_fav=in_fav, in_watch=in_watch)

@app.route('/recommend/<title>')
def recommend(title):
    recommendations = recommend_movies(title)
    for rec in recommendations:
        rec['poster'] = get_movie_poster(rec['title'], rec.get('year'))
    return render_template('recommendations.html', title=title, recommendations=recommendations)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash("Username or email already exists.", "danger")
            return redirect(url_for('register'))
        user = User(username=username, email=email, password_hash=generate_password_hash(password), is_admin=False)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('login.html', mode='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for('index'))
        flash("Invalid username or password.", "danger")
    return render_template('login.html', mode='login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for('index'))

@app.route('/add_favorite', methods=['POST'])
@login_required
def add_favorite():
    title = request.form.get('movie_title')
    if title:
        if not Favorite.query.filter_by(user_id=current_user.id, movie_title=title).first():
            fav = Favorite(user_id=current_user.id, movie_title=title)
            db.session.add(fav)
            db.session.commit()
            flash(f"Added {title} to favorites!", "success")
    return redirect(request.referrer or url_for('index'))

@app.route('/remove_favorite', methods=['POST'])
@login_required
def remove_favorite():
    title = request.form.get('movie_title')
    fav = Favorite.query.filter_by(user_id=current_user.id, movie_title=title).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
        flash(f"Removed from favorites.", "info")
    return redirect(request.referrer or url_for('index'))

@app.route('/add_watchlist', methods=['POST'])
@login_required
def add_watchlist():
    title = request.form.get('movie_title')
    if title:
        if not Watchlist.query.filter_by(user_id=current_user.id, movie_title=title).first():
            wl = Watchlist(user_id=current_user.id, movie_title=title)
            db.session.add(wl)
            db.session.commit()
            flash(f"Added {title} to watchlist!", "success")
    return redirect(request.referrer or url_for('index'))

@app.route('/remove_watchlist', methods=['POST'])
@login_required
def remove_watchlist():
    title = request.form.get('movie_title')
    wl = Watchlist.query.filter_by(user_id=current_user.id, movie_title=title).first()
    if wl:
        db.session.delete(wl)
        db.session.commit()
        flash(f"Removed from watchlist.", "info")
    return redirect(request.referrer or url_for('index'))

@app.route('/profile')
@login_required
def profile():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    watchlist = Watchlist.query.filter_by(user_id=current_user.id).all()
    history = RecommendationHistory.query.filter_by(user_id=current_user.id).order_by(RecommendationHistory.created_at.desc()).limit(20).all()
    favorites_data = []
    for f in favorites:
        favorites_data.append({'title': f.movie_title, 'poster': get_movie_poster(f.movie_title)})
    watchlist_data = []
    for w in watchlist:
        watchlist_data.append({'title': w.movie_title, 'poster': get_movie_poster(w.movie_title)})
    return render_template('profile.html', favorites=favorites_data, watchlist=watchlist_data, history=history)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('index'))
    users = User.query.all()
    total_users = len(users)
    total_favs = Favorite.query.count()
    total_watch = Watchlist.query.count()
    return render_template('admin.html', users=users, total_users=total_users, total_favs=total_favs, total_watch=total_watch)

@app.route('/admin/add_movie', methods=['POST'])
@login_required
def admin_add_movie():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('admin_dashboard'))
    title = request.form.get('title')
    genres = request.form.get('genres')
    overview = request.form.get('overview')
    cast = request.form.get('cast')
    director = request.form.get('director')
    rating = request.form.get('rating')
    year = request.form.get('year')
    if title:
        df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'movies.csv'))
        new_row = pd.DataFrame([{
            'title': title,
            'genres': genres,
            'overview': overview,
            'cast': cast,
            'director': director,
            'rating': float(rating or 7.0),
            'year': int(year or 2024),
            'keywords': genres
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(os.path.join(os.path.dirname(__file__), 'movies.csv'), index=False)
        build_model()
        flash(f"Added {title}.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_movie', methods=['POST'])
@login_required
def admin_delete_movie():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('admin_dashboard'))
    title = request.form.get('movie_title')
    if title:
        df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'movies.csv'))
        df = df[df['title'] != title]
        df.to_csv(os.path.join(os.path.dirname(__file__), 'movies.csv'), index=False)
        build_model()
        flash(f"Deleted {title}.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_user/<int:user_id>', methods=['POST'])
@login_required
def admin_update_user(user_id):
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for('admin_dashboard'))
    user = User.query.get(user_id)
    if user:
        user.is_admin = bool(request.form.get('is_admin'))
        db.session.commit()
        flash("User updated.", "success")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
