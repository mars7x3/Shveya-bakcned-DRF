from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from nested_admin.nested import NestedStackedInline, NestedModelAdmin

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

admin.site.register(Combination)
admin.site.register(Equipment)
admin.site.register(Operation)
admin.site.register(CombinationFile)
admin.site.register(Color)


class ConsumableInline(NestedStackedInline):
    model = Consumable
    extra = 0


class OperationInline(NestedStackedInline):
    model = Operation
    extra = 0


class PatternInline(NestedStackedInline):
    model = Pattern
    extra = 0


class NomCountInline(NestedStackedInline):
    model = NomCount
    extra = 0


@admin.register(Nomenclature)
class NomenclatureAdmin(NestedModelAdmin):
    pass
    # inlines = (NomCountInline, PatternInline, OperationInline)
    # list_display = ("id", "title", "vendor_code")
    # list_display_links = ("id", "title", "vendor_code")
    # search_fields = ("id", "title", "vendor_code")

# ______________________________ Nomenclature end ______________________________


# ______________________________ Warehouse ______________________________

admin.site.register(Warehouse)


class QuantityNomenclatureInline(NestedStackedInline):
    model = QuantityNomenclature
    extra = 0


class QuantityHistoryInline(NestedStackedInline):
    model = QuantityHistory
    extra = 0


class QuantityFileInline(NestedStackedInline):
    model = QuantityFile
    extra = 0


@admin.register(Quantity)
class QuantityAdmin(NestedModelAdmin):
    inlines = (QuantityNomenclatureInline, QuantityFileInline, QuantityHistoryInline)
    list_display = ("id", "in_warehouse", "out_warehouse", "status", "created_at")
    list_display_links = ("id", "in_warehouse", "out_warehouse", "status", "created_at")

# ______________________________ Warehouse end ______________________________


# ______________________________ Order ______________________________

class OrderProductAmountInline(NestedStackedInline):
    model = OrderProductAmount
    extra = 0


class OrderProductInline(NestedStackedInline):
    model = OrderProduct
    extra = 0
    inlines = (OrderProductAmountInline,)


@admin.register(Order)
class OrderAdmin(NestedModelAdmin):
    inlines = (OrderProductInline,)
    list_display = ("id", "status", "deadline", "created_at")
    list_display_links = ("id", "status", "deadline", "created_at")

# ______________________________ Order end ______________________________


# ______________________________ Work ______________________________

class WorkDetailInline(NestedStackedInline):
    model = WorkDetail
    extra = 0


# @admin.register(Work)
# class WorkAdmin(NestedModelAdmin):
#     inlines = (WorkDetailInline,)
#     list_display = ("id", "staff", "order", "status", "created_at")
#     list_display_links = ("id", "staff", "order", "status", "created_at")

# ______________________________ Work end ______________________________


# ______________________________ Payment ______________________________

class PaymentFileInline(NestedStackedInline):
    model = PaymentFile
    extra = 0


@admin.register(Payment)
class PaymentAdmin(NestedModelAdmin):
    inlines = (PaymentFileInline,)
    list_display = ("id", "staff", "status", "created_at")
    list_display_links = ("id", "staff", "status", "created_at")

# ______________________________ Payment end ______________________________
