"""from django.contrib import admin
from .models import FoodWaste

admin.site.register(FoodWaste)"""
from django.contrib import admin
from .models import FoodEntry,CloseDayEntry

@admin.register(FoodEntry)
class FoodEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'dal', 'chawal', 'sabji')

@admin.register(CloseDayEntry)
class CloseDayEntry(admin.ModelAdmin):
    list_display = ('user', 'date',
                     'sold_dal', 'sold_chawal', 'sold_sabji')

