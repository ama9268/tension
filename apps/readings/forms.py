from django import forms
from django.utils import timezone

from .models import BloodPressureReading


class BloodPressureReadingForm(forms.ModelForm):
    measured_at = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
        label="Fecha y hora",
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = BloodPressureReading
        fields = ["systolic", "diastolic", "pulse", "measured_at", "time_of_day", "notes"]
        labels = {
            "systolic": "Sistólica (mmHg)",
            "diastolic": "Diastólica (mmHg)",
            "pulse": "Pulso (ppm)",
            "time_of_day": "Momento del día",
            "notes": "Notas",
        }
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            now = timezone.localtime(timezone.now())
            self.fields["measured_at"].initial = now.strftime("%Y-%m-%dT%H:%M")
