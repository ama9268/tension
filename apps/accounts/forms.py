from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo electrónico")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class UserProfileForm(forms.ModelForm):
    medical_context = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        required=False,
        label="Contexto médico personal",
        help_text=(
            "El agente IA incluirá este texto en cada análisis. "
            "Escribe lo que consideres relevante: edad, peso, actividad física, "
            "tipo de trabajo, medicación habitual, antecedentes, etc."
        ),
    )

    class Meta:
        model = UserProfile
        fields = ("medical_context",)
