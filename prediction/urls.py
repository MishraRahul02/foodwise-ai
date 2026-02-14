from django.urls import path
from .views import predict_waste

urlpatterns = [
    path("predict/", predict_waste, name="predict_waste"),
]
