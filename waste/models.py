from django.db import models

class FoodWaste(models.Model):
    date = models.DateField(auto_now_add=True)
    food_prepared = models.FloatField()
    food_sold = models.FloatField()
    food_wasted = models.FloatField()
    is_event_day = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.date} - Waste: {self.food_wasted}"
