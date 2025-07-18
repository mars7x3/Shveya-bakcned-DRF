from rest_framework.permissions import BasePermission

from my_db.enums import UserStatus, StaffRole


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return UserStatus.STAFF == request.user.status


class IsDirectorAndTechnologist(BasePermission):
    def has_permission(self, request, view):
        return request.user.staff_profile.role in [StaffRole.DIRECTOR, StaffRole.TECHNOLOGIST]


class IsDirectorAndTechnologistAndWarehouse(BasePermission):
    def has_permission(self, request, view):
        return request.user.staff_profile.role in [StaffRole.DIRECTOR, StaffRole.TECHNOLOGIST, StaffRole.WAREHOUSE]


class IsWarehouse(BasePermission):
    def has_permission(self, request, view):
        return request.user.staff_profile.role == StaffRole.WAREHOUSE


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.staff_profile == obj.staff


class IsCutter(BasePermission):
    def has_permission(self, request, view):
        return request.user.staff_profile.role == StaffRole.CUTTER


class IsController(BasePermission):
    def has_permission(self, request, view):
        return request.user.staff_profile.role == StaffRole.CONTROLLER


class IsAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.staff == request.user.staff_profile


class ClientIsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.client == request.user.client_profile
