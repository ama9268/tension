from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "has_medical_context", "created_at"]
    raw_id_fields = ["user"]
    readonly_fields = ["created_at"]

    @admin.display(boolean=True, description="Contexto médico")
    def has_medical_context(self, obj):
        return bool(obj.medical_context)
