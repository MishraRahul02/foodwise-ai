# ================================
# Django & Auth Imports
# ================================
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect

# ================================
# App Models
# ================================
from .models import FoodEntry, CloseDayEntry, FoodRequest

# ================================
# Python Utilities
# ================================
from pathlib import Path
import csv
import os

# ================================
# ML Model Loading
# ================================
from joblib import load
from django.conf import settings

# ML model paths
DAL_MODEL_PATH = os.path.join(settings.BASE_DIR, "models", "dal_model.pkl")
CHAWAL_MODEL_PATH = os.path.join(settings.BASE_DIR, "models", "chawal_model.pkl")
SABJI_MODEL_PATH = os.path.join(settings.BASE_DIR, "models", "sabji_model.pkl")

# Load ML models once (server start pe)
dal_model = load(DAL_MODEL_PATH)
chawal_model = load(CHAWAL_MODEL_PATH)
sabji_model = load(SABJI_MODEL_PATH)


# ================================
# Helper Functions
# ================================

def parse_qty(qty):
    """
    Form se aane wali quantity ko numeric me convert karta hai.
    Example:
    "5 plates" -> 5
    "10" -> 10
    """
    if not qty:
        return 0
    try:
        return int(str(qty).split()[0])
    except:
        return 0


def get_latest_entry(model, user, date):
    """
    Kisi user ke liye given date par agar multiple entries hain
    to latest wali entry return karta hai.
    """
    return model.objects.filter(user=user, date=date).order_by('-id').first()


def build_ml_features_for_day(user, date):
    """
    ML model ke liye required features database se collect karta hai.
    """
    planned = get_latest_entry(FoodEntry, user, date)
    closed = get_latest_entry(CloseDayEntry, user, date)

    if not planned or not closed:
        return None

    return {
        "day_of_week": date.weekday(),
        "dal_added": parse_qty(planned.dal),
        "chawal_added": parse_qty(planned.chawal),
        "sabji_added": parse_qty(planned.sabji),
        "dal_sold": parse_qty(closed.sold_dal),
        "chawal_sold": parse_qty(closed.sold_chawal),
        "sabji_sold": parse_qty(closed.sold_sabji),
        "dal_waste": closed.dal_waste,
        "chawal_waste": closed.chawal_waste,
        "sabji_waste": closed.sabji_waste,
    }


def append_ml_row_to_csv(features):
    """
    Har din ka ML training data CSV file me store karta hai
    jisse future me model retrain ho sake.
    """
    file_path = Path("ml_data.csv")
    file_exists = file_path.exists()

    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(features.keys())
        writer.writerow(features.values())


def calculate_remaining(planned, closed):
    """
    Donation section ke liye:
    bacha hua food = planned - sold
    """
    dal = max(parse_qty(planned.dal) - parse_qty(closed.sold_dal), 0)
    chawal = max(parse_qty(planned.chawal) - parse_qty(closed.sold_chawal), 0)
    sabji = max(parse_qty(planned.sabji) - parse_qty(closed.sold_sabji), 0)
    return dal, chawal, sabji


# ================================
# Public Home Page
# ================================
def home(request):
    """
    Home page:
    Sabhi restaurants ka bacha hua food show hota hai
    taaki needy log request kar sakein.
    """
    today = now().date()
    donations = []

    planned_list = FoodEntry.objects.filter(date=today)

    for planned in planned_list:
        closed = get_latest_entry(CloseDayEntry, planned.user, today)
        if not closed:
            continue

        dal, chawal, sabji = calculate_remaining(planned, closed)
        if dal or chawal or sabji:
            donations.append({
                "restaurant": planned.user.username,
                "dal": dal,
                "chawal": chawal,
                "sabji": sabji,
            })

    return render(request, "index.html", {"donations": donations})


# ================================
# Auth & Dashboard
# ================================
def register(request):
    """
    New restaurant owner ka registration
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("restaurant_dashboard")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})


@never_cache
@login_required
def restaurant_dashboard(request):
    """
    Restaurant owner ka dashboard:
    - Aaj ka planned food
    - Aaj ka sold/waste food
    - Aayi hui food requests
    """
    today = now().date()
    planned = get_latest_entry(FoodEntry, request.user, today)
    closed = get_latest_entry(CloseDayEntry, request.user, today)

    requests = FoodRequest.objects.filter(
        restaurant=request.user
    ).order_by("-created_at")

    return render(request, "restaurant_dashboard.html", {
        "planned": planned,
        "closed": closed,
        "requests": requests,
    })


# ================================
# Add Food (Morning)
# ================================
@never_cache
@login_required
def add_food(request):
    """
    Subah ka banaya hua food enter karne ka page
    """
    if request.method == "POST":
        today = now().date()

        dal_qty = request.POST.get('dal_qty')
        chawal_qty = request.POST.get('chawal_qty')
        sabji_qty = request.POST.get('sabji_qty')

        planned = get_latest_entry(FoodEntry, request.user, today)

        if planned:
            planned.dal = dal_qty
            planned.chawal = chawal_qty
            planned.sabji = sabji_qty
            planned.save()
        else:
            FoodEntry.objects.create(
                user=request.user,
                dal=dal_qty,
                chawal=chawal_qty,
                sabji=sabji_qty,
                date=today
            )

        messages.success(request, "Today's planned food updated successfully ✅")
        return redirect("restaurant_dashboard")

    return render(request, 'add_food.html')


# ================================
# Close Day (Night)
# ================================
@never_cache
@login_required
def close_day(request):
    """
    Raat ko sold food aur waste calculate hota hai
    """
    if request.method == "POST":
        today = now().date()

        planned = get_latest_entry(FoodEntry, request.user, today)

        sold_dal = request.POST.get('sold_dal')
        sold_chawal = request.POST.get('sold_chawal')
        sold_sabji = request.POST.get('sold_sabji')

        closed = get_latest_entry(CloseDayEntry, request.user, today)

        dal_waste = chawal_waste = sabji_waste = 0

        if planned:
            dal_waste = max(parse_qty(planned.dal) - parse_qty(sold_dal), 0)
            chawal_waste = max(parse_qty(planned.chawal) - parse_qty(sold_chawal), 0)
            sabji_waste = max(parse_qty(planned.sabji) - parse_qty(sold_sabji), 0)

        if closed:
            closed.sold_dal = sold_dal
            closed.sold_chawal = sold_chawal
            closed.sold_sabji = sold_sabji
            closed.dal_waste = dal_waste
            closed.chawal_waste = chawal_waste
            closed.sabji_waste = sabji_waste
            closed.save()
        else:
            CloseDayEntry.objects.create(
                user=request.user,
                sold_dal=sold_dal,
                sold_chawal=sold_chawal,
                sold_sabji=sold_sabji,
                dal_waste=dal_waste,
                chawal_waste=chawal_waste,
                sabji_waste=sabji_waste,
                date=today
            )

        features = build_ml_features_for_day(request.user, today)
        if features:
            append_ml_row_to_csv(features)

        messages.success(request, "Day closed successfully ✅")
        return redirect("restaurant_dashboard")

    return render(request, 'close_day.html')


# ================================
# Prediction
# ================================
@never_cache
@login_required
def predict_page(request):
    """
    Kal ke liye kitna dal, chawal, sabji banana chahiye
    iska ML-based prediction show karta hai.
    """

    dal_pred = chawal_pred = sabji_pred = None

    if request.method == "POST":
        today = now().date()
        planned = get_latest_entry(FoodEntry, request.user, today)
        closed = get_latest_entry(CloseDayEntry, request.user, today)

        if planned and closed:
            # ✅ Day of week (0 = Monday, 6 = Sunday)
            day_of_week = int(today.weekday())

            # ✅ Safe numeric conversion (string -> int)
            dal_added = int(parse_qty(planned.dal))
            chawal_added = int(parse_qty(planned.chawal))
            sabji_added = int(parse_qty(planned.sabji))

            dal_sold = int(parse_qty(closed.sold_dal))
            chawal_sold = int(parse_qty(closed.sold_chawal))
            sabji_sold = int(parse_qty(closed.sold_sabji))

            dal_waste = int(closed.dal_waste or 0)
            chawal_waste = int(closed.chawal_waste or 0)
            sabji_waste = int(closed.sabji_waste or 0)

            # ✅ Final ML input (pure numbers only)
            dal_input = [[day_of_week, dal_added, dal_sold, dal_waste]]
            chawal_input = [[day_of_week, chawal_added, chawal_sold, chawal_waste]]
            sabji_input = [[day_of_week, sabji_added, sabji_sold, sabji_waste]]

            # 🔮 ML Predictions
            dal_pred = round(float(dal_model.predict(dal_input)[0]))
            chawal_pred = round(float(chawal_model.predict(chawal_input)[0]))
            sabji_pred = round(float(sabji_model.predict(sabji_input)[0]))

            # ✅ Business logic: kam se kam aaj ke sold se thoda zyada cook karo
            dal_baseline = int(dal_sold * 1.1)
            chawal_baseline = int(chawal_sold * 1.1)
            sabji_baseline = int(sabji_sold * 1.1)

            dal_pred = max(1, dal_pred, dal_baseline)
            chawal_pred = max(1, chawal_pred, chawal_baseline)
            sabji_pred = max(1, sabji_pred, sabji_baseline)

    return render(request, 'predict.html', {
        "dal_pred": dal_pred,
        "chawal_pred": chawal_pred,
        "sabji_pred": sabji_pred,
    })

# ================================
# Food Request System
# ================================
@csrf_protect
def request_food(request, restaurant_username):
    """
    Public user food request karta hai
    """
    restaurant = get_object_or_404(User, username=restaurant_username)

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")

        req = FoodRequest.objects.create(
            restaurant=restaurant,
            requester_name=name,
            requester_phone=phone,
            status="pending"
        )

        messages.success(request, "Your request has been sent.")
        return redirect("request_status", req_id=req.id)

    return render(request, "request_food.html", {"restaurant": restaurant})


def request_status(request, req_id):
    """
    User apni request ka status check karta hai
    """
    req = get_object_or_404(FoodRequest, id=req_id)
    return render(request, "request_status.html", {"req": req})


@login_required
def accept_request(request, req_id):
    req = get_object_or_404(FoodRequest, id=req_id, restaurant=request.user)
    req.status = "accepted"
    req.save()
    return redirect("restaurant_dashboard")


@login_required
def reject_request(request, req_id):
    req = get_object_or_404(FoodRequest, id=req_id, restaurant=request.user)
    req.status = "rejected"
    req.save()
    return redirect("restaurant_dashboard")


@login_required
def delete_request(request, req_id):
    req = get_object_or_404(FoodRequest, id=req_id, restaurant=request.user)
    req.delete()
    return redirect("restaurant_dashboard")

@login_required
def delete_all_requests(request):
    """
    Owner ke saare food requests ek click me delete karta hai
    """
    FoodRequest.objects.filter(restaurant=request.user).delete()
    messages.success(request, "All food requests deleted successfully 🗑️")
    return redirect("restaurant_dashboard")
