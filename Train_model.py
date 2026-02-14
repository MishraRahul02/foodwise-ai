import os
import django
import pandas as pd
from sklearn.linear_model import LinearRegression
from joblib import dump

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Waste_Food_System.settings")
django.setup()

from core.models import FoodEntry, CloseDayEntry


def parse_qty(qty):
    if not qty:
        return 0
    try:
        return int(str(qty).split()[0])
    except:
        return 0


rows = []

# Collect historical data
entries = FoodEntry.objects.all().order_by("user", "date")

for entry in entries:
    closed = CloseDayEntry.objects.filter(user=entry.user, date=entry.date).first()
    if not closed:
        continue

    rows.append({
        "day_of_week": entry.date.weekday(),

        "dal_added": parse_qty(entry.dal),
        "chawal_added": parse_qty(entry.chawal),
        "sabji_added": parse_qty(entry.sabji),

        "dal_sold": parse_qty(closed.sold_dal),
        "chawal_sold": parse_qty(closed.sold_chawal),
        "sabji_sold": parse_qty(closed.sold_sabji),

        "dal_waste": closed.dal_waste,
        "chawal_waste": closed.chawal_waste,
        "sabji_waste": closed.sabji_waste,

        # targets (we'll shift later)
        "target_dal": parse_qty(entry.dal),
        "target_chawal": parse_qty(entry.chawal),
        "target_sabji": parse_qty(entry.sabji),
    })

df = pd.DataFrame(rows)

if df.empty or len(df) < 10:
    print("❌ Not enough data to train model. Add more days of data.")
    exit()

# Shift targets to represent next day cooking (simple baseline)
df["target_dal"] = df["target_dal"].shift(-1)
df["target_chawal"] = df["target_chawal"].shift(-1)
df["target_sabji"] = df["target_sabji"].shift(-1)
df = df.dropna()

# Train separate models
X_dal = df[["day_of_week", "dal_added", "dal_sold", "dal_waste"]]
y_dal = df["target_dal"]

X_chawal = df[["day_of_week", "chawal_added", "chawal_sold", "chawal_waste"]]
y_chawal = df["target_chawal"]

X_sabji = df[["day_of_week", "sabji_added", "sabji_sold", "sabji_waste"]]
y_sabji = df["target_sabji"]

dal_model = LinearRegression().fit(X_dal, y_dal)
chawal_model = LinearRegression().fit(X_chawal, y_chawal)
sabji_model = LinearRegression().fit(X_sabji, y_sabji)

# Save models
os.makedirs("models", exist_ok=True)
dump(dal_model, "models/dal_model.pkl")
dump(chawal_model, "models/chawal_model.pkl")
dump(sabji_model, "models/sabji_model.pkl")

print("✅ Models trained & saved: models/dal_model.pkl, chawal_model.pkl, sabji_model.pkl")
