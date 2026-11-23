from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView

from .forms import RegisterForm, UserProfileForm
from .models import ApiKey, UserProfile


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["api_keys"] = ApiKey.objects.filter(user=self.request.user)
        ctx["new_api_key"] = self.request.session.pop("new_api_key", None)
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Contexto médico actualizado correctamente.")
        return super().form_valid(form)


class ApiKeyCreateView(LoginRequiredMixin, View):
    def post(self, request):
        name = request.POST.get("name", "").strip()[:80] or "Sin nombre"
        _, raw = ApiKey.create_for(request.user, name)
        request.session["new_api_key"] = raw  # se muestra una sola vez
        return redirect("profile")


class ApiKeyRevokeView(LoginRequiredMixin, View):
    def post(self, request, pk: int):
        key = get_object_or_404(ApiKey, pk=pk, user=request.user)
        key.revoked = True
        key.save(update_fields=["revoked"])
        messages.success(request, "API key revocada.")
        return redirect("profile")
