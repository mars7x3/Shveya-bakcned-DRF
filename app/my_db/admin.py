from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import *

# ______________________________ User ______________________________

@admin.register(MyUser)
class MyUserAdmin(UserAdmin):
    list_display = ("id", "username", "status", "is_active")
    list_display_links = ("id", "username", "status", "is_active")
    search_fields = ("username", "id")

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            }
        ),
        (
            _("Advanced options"),
            {
                "classes": ("wide",),
                "fields": ("status",),
            }
        )
    )
    fieldsets = (
        (_("Personal info"), {"fields": ("username", "password", "status")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "surname", "role")
    list_display_links = ("id", "name", "surname", "role")
    search_fields = ("id", "name")


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "surname", "company_title")
    list_display_links = ("id", "name", "surname", "company_title")
    search_fields = ("id", "name", "company_title")

# ______________________________ User end ______________________________


# ______________________________ General ______________________________

@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "percent")
    list_display_links = ("id", "title", "percent")


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
    list_display_links = ("id", "title")

# ______________________________ General end ______________________________


# ______________________________ Nomenclature ______________________________

class PatternInline(admin.StackedInline):
    model = Pattern
    extra = 0


@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    inlines = (PatternInline,)
    list_display = ("id", "title", "vendor_code")
    list_display_links = ("id", "title", "vendor_code")
    search_fields = ("id", "title", "vendor_code")

# ______________________________ Nomenclature end ______________________________