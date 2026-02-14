# FoodWise AI 🍽️🌱

FoodWise AI is a Django + Machine Learning based web application to reduce food waste in restaurants.

## 🚀 Features
- Daily food planning & end-of-day closing
- AI-based prediction for next day food preparation
- Real-time food donation listing for NGOs / users
- Food request system with accept / reject by restaurant owners
- Dashboard for restaurants to track waste and optimize cooking

## 🧠 Tech Stack
- Backend: Django
- ML: Scikit-learn (Linear Regression models)
- Database: SQLite (can be extended to PostgreSQL)
- Frontend: HTML, CSS, Bootstrap

## 🎯 Goal
Reduce food wastage using data-driven prediction and enable leftover food donation to help people in need.

## ⚙️ Setup (Local)
```bash
git clone https://github.com/MishraRahul02/foodwise-ai.git
cd foodwise-ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
