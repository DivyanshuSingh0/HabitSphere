from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import json
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///habits.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    habits = db.relationship('Habit', backref='user', lazy=True)
    badges = db.relationship('Badge', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entries = db.relationship('HabitEntry', backref='habit', lazy=True)
    
    @property
    def current_streak(self):
        entries = sorted([e.date for e in self.entries], reverse=True)
        if not entries:
            return 0
        
        streak = 1
        for i in range(len(entries)-1):
            if (entries[i] - entries[i+1]).days == 1:
                streak += 1
            else:
                break
        return streak

class HabitEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.String(200))

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
@login_required
def index():
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', habits=habits)

@app.route('/add_habit', methods=['POST'])
@login_required
def add_habit():
    name = request.form.get('name')
    description = request.form.get('description')
    
    habit = Habit(name=name, description=description, user_id=current_user.id)
    db.session.add(habit)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/log_entry/<int:habit_id>', methods=['POST'])
@login_required
def log_entry(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    if habit.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    entry = HabitEntry(habit_id=habit_id, notes=request.form.get('notes'))
    db.session.add(entry)
    db.session.commit()
    
    # Check for streak-based badges
    streak = habit.current_streak
    if streak == 7:
        badge = Badge(name="Week Warrior", description="7 day streak!", user_id=current_user.id)
        db.session.add(badge)
    elif streak == 30:
        badge = Badge(name="Monthly Master", description="30 day streak!", user_id=current_user.id)
        db.session.add(badge)
    db.session.commit()
    
    return redirect(url_for('index'))

@app.route('/predict/<int:habit_id>')
@login_required
def predict_success(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    if habit.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    entries = HabitEntry.query.filter_by(habit_id=habit_id).all()
    if len(entries) < 7:  # Need at least a week of data
        return jsonify({'prediction': 'Need more data (at least 7 days)'})
    
    # Prepare data for ML
    dates = [e.date for e in entries]
    streak_data = []
    success_data = []
    
    for i in range(len(dates)-7):
        week_entries = dates[i:i+7]
        next_day = any(d for d in dates if (week_entries[-1] + timedelta(days=1)).date() == d.date())
        
        # Features: current streak, day of week, time between entries
        streak = 1
        for j in range(len(week_entries)-1):
            if (week_entries[j] - week_entries[j+1]).days == 1:
                streak += 1
            else:
                break
        
        streak_data.append([
            streak,
            week_entries[-1].weekday(),
            (week_entries[-1] - week_entries[-2]).total_seconds() / 3600
        ])
        success_data.append(1 if next_day else 0)
    
    if not streak_data:  # If not enough consecutive data
        return jsonify({'prediction': 'Need more consecutive data'})
    
    # Train model
    model = RandomForestClassifier(n_estimators=100)
    model.fit(streak_data, success_data)
    
    # Predict for tomorrow
    latest_streak = habit.current_streak
    latest_entry = entries[-1]
    
    prediction = model.predict_proba([[
        latest_streak,
        (latest_entry.date + timedelta(days=1)).weekday(),
        24  # Assuming next entry would be in 24 hours
    ]])[0][1]
    
    return jsonify({'prediction': f'{prediction:.1%}'})

@app.route('/analytics/<int:habit_id>')
@login_required
def analytics(habit_id):
    habit = Habit.query.get_or_404(habit_id)
    if habit.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    entries = HabitEntry.query.filter_by(habit_id=habit_id).all()
    dates = [e.date for e in entries]
    
    # Calculate various metrics
    total_entries = len(entries)
    current_streak = habit.current_streak
    
    # Calculate 30-day completion rate
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_entries = [d for d in dates if d >= thirty_days_ago]
    completion_rate = len(recent_entries) / 30.0
    
    # Prepare data for daily chart (last 30 days)
    date_range = pd.date_range(end=datetime.utcnow().date(), periods=30)
    daily_series = pd.Series([d.date() for d in dates])
    daily_counts = daily_series.value_counts().reindex(date_range.date, fill_value=0)
    
    # Prepare data for weekly chart
    weekly_series = pd.Series([d.isocalendar()[1] for d in dates])
    current_week = datetime.utcnow().isocalendar()[1]
    week_range = range(current_week - 11, current_week + 1)  # Last 12 weeks
    weekly_counts = weekly_series.value_counts().reindex(week_range, fill_value=0)
    
    # Convert dates to string format for JSON serialization
    daily_data = {d.strftime('%Y-%m-%d'): int(c) for d, c in daily_counts.items()}
    weekly_data = {f'Week {w}': int(c) for w, c in weekly_counts.items()}
    
    return render_template(
        'analytics.html',
        habit=habit,
        total_entries=total_entries,
        current_streak=current_streak,
        completion_rate=completion_rate,
        daily_data=json.dumps(daily_data),
        weekly_data=json.dumps(weekly_data)
    )

def award_welcome_badge(user):
    """Award the welcome badge to new users if they don't have it"""
    welcome_badge = Badge.query.filter_by(user_id=user.id, name='Welcome!').first()
    if not welcome_badge:
        welcome_badge = Badge(
            name='Welcome!',
            description='Joined HabitSphere and started their journey to better habits',
            user_id=user.id
        )
        db.session.add(welcome_badge)
        db.session.commit()

@app.route('/profile')
@login_required
def profile():
    try:
        # Get total habits for the user
        total_habits = Habit.query.filter_by(user_id=current_user.id).count()
        
        # Get total habit entries (check-ins)
        total_entries = HabitEntry.query.join(Habit).filter(Habit.user_id == current_user.id).count()
        
        # Ensure user has welcome badge
        award_welcome_badge(current_user)
        
        # Get user's badges
        badges = Badge.query.filter_by(user_id=current_user.id).order_by(Badge.earned_at.desc()).all()
        total_badges = len(badges)
        
        return render_template('profile.html', 
                             total_habits=total_habits,
                             total_entries=total_entries,
                             total_badges=total_badges,
                             badges=badges)
    except Exception as e:
        flash('An error occurred while loading your profile. Please try again.', 'danger')
        return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Award welcome badge to new user
        award_welcome_badge(user)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
