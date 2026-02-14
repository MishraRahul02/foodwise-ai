from django.shortcuts import render
import pandas as pd
from sklearn.linear_model import LinearRegression
from waste.models import FoodWaste   # 👈 model waste app se aayega

def predict_waste(request):
    prediction = None

    if request.method == "POST":
        prepared = float(request.POST.get("prepared"))
        event = int(request.POST.get("event"))

        data = FoodWaste.objects.all().values()
        df = pd.DataFrame(data)

        X = df[['food_prepared', 'is_event_day']]
        y = df['food_wasted']

        model = LinearRegression()
        model.fit(X, y)

        input_data = pd.DataFrame(
            [[prepared, event]],
            columns=['food_prepared', 'is_event_day']
        )

        prediction = round(model.predict(input_data)[0], 2)

    return render(request, "predict.html", {"prediction": prediction})
