# HabitSphere 🌟

HabitSphere is an intelligent habit tracking platform that combines machine learning insights with gamification to help you build and maintain positive habits. Built with Flask and powered by scikit-learn, it provides personalized predictions and insights to support your personal growth journey.

## ✨ Features

- **🔐 Secure User Authentication**
  - Personal account creation and management
  - Secure password hashing
  - Session management

- **📊 Habit Tracking**
  - Create and manage multiple habits
  - Daily check-ins and streak tracking
  - Detailed progress visualization
  - Weekly and monthly analytics

- **🤖 Machine Learning Insights**
  - Habit completion predictions
  - Pattern recognition
  - Personalized recommendations

- **🎮 Gamification**
  - Achievement badges
  - Streak tracking
  - Progress milestones
  - Visual rewards

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/habitsphere.git
   cd habitsphere
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Unix or MacOS:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables
   ```bash
   copy .env.example .env
   ```
   Edit `.env` with your configuration

6. Initialize the database
   ```bash
   python
   >>> from app import app, db
   >>> app.app_context().push()
   >>> db.create_all()
   >>> exit()
   ```

7. Run the application
   ```bash
   python app.py
   ```

Visit `http://localhost:5000` in your browser to start using HabitSphere!

## 🛠️ Technology Stack

- **Backend**: Flask
- **Database**: SQLAlchemy with SQLite
- **Authentication**: Flask-Login
- **ML**: scikit-learn
- **Frontend**: Bootstrap 5, Chart.js
- **Icons**: Font Awesome

## 📱 Features in Detail

### Habit Management
- Create custom habits with descriptions
- Set frequency and reminders
- Track progress with daily check-ins
- View detailed statistics and trends

### Analytics Dashboard
- Visual progress tracking
- Completion rate statistics
- Streak information
- Prediction insights

### Achievement System
- Welcome badge for new users
- Milestone badges (7-day, 30-day streaks)
- Special achievement badges
- Progress-based rewards

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Flask and its extensions developers
- scikit-learn team
- Bootstrap team
- All contributors and users

## 📞 Contact

Your Name - [@yourusername](https://twitter.com/yourusername)

Project Link: [https://github.com/yourusername/habitsphere](https://github.com/yourusername/habitsphere)
