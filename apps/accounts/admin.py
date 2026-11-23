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


from .models import ApiKey  # noqa: E402


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "prefix", "revoked", "created_at", "last_used_at"]
    list_filter = ["revoked"]
    raw_id_fields = ["user"]
    readonly_fields = ["prefix", "created_at", "last_used_at"]
    exclude = ["key_hash"]
