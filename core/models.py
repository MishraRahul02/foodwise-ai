from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


class FoodEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    dal = models.CharField(max_length=100, blank=True)
    chawal = models.CharField(max_length=100, blank=True)
    sabji = models.CharField(max_length=100, blank=True)

    date = models.DateField(default=now)

    def __str__(self):
        return f"Planned - {self.user.username} - {self.date}"


class CloseDayEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # SOLD FOOD ONLY
    sold_dal = models.CharField(max_length=100, blank=True)
    sold_chawal = models.CharField(max_length=100, blank=True)
    sold_sabji = models.CharField(max_length=100, blank=True)
    date = models.DateField(default=now)

    chawal_waste = models.CharField(default=0)
    sabji_waste = models.CharField(default=0)
    dal_waste = models.CharField(default=0)

    def __str__(self):
        return f"Close Day - {self.user.username} - {self.date}"


from django.db import models
from django.contrib.auth.models import User

class FoodRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )

    restaurant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_requests")
    requester_name = models.CharField(max_length=100)
    requester_phone = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.requester_name} -> {self.restaurant.username}"
