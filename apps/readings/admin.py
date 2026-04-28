from django.contrib import admin

from .models import BloodPressureReading


@admin.register(BloodPressureReading)
class BloodPressureReadingAdmin(admin.ModelAdmin):
    list_display = [
        "user", "systolic", "diastolic", "pulse",
        "measured_at", "time_of_day", "classification_label",
    ]
    list_filter = ["time_of_day", "measured_at", "user"]
    search_fields = ["user__username", "notes"]
    date_hierarchy = "measured_at"
    readonly_fields = ["created_at"]
