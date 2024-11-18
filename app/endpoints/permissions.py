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


class IsWarehouse(BasePermission):
    def has_permission(self, request, view):
        if request.user.staff_profile.role == StaffRole.WAREHOUSE:
            return True
        return False