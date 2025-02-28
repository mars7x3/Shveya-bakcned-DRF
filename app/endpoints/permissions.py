from rest_framework.permissions import BasePermission

from my_db.enums import UserStatus, StaffRole


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        if UserStatus.STAFF == request.user.status:
            return True
        return False


class IsDirectorAndTechnologist(BasePermission):
    def has_permission(self, request, view):
        if request.user.staff_profile.role in [StaffRole.DIRECTOR, StaffRole.TECHNOLOGIST]:
            return True
        return False


class IsDirectorAndTechnologistAndWarehouse(BasePermission):
    def has_permission(self, request, view):
        if request.user.staff_profile.role in [StaffRole.DIRECTOR, StaffRole.TECHNOLOGIST, StaffRole.WAREHOUSE]:
            return True
        return False


class IsWarehouse(BasePermission):
    def has_permission(self, request, view):
        if request.user.staff_profile.role == StaffRole.WAREHOUSE:
            return True
        return False


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.staff_profile == obj.staff:
            return True
        return False


class IsCutter(BasePermission):
    def has_permission(self, request, view):
        if request.user.staff_profile.role == StaffRole.CUTTER:
            return True
        return False

