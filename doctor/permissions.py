from rest_framework.permissions import BasePermission
from .models import Doctor

class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        # Check if user is authenticated and linked to an approved Doctor
        if not request.user.is_authenticated:
            return False
        try:
            doctor = request.user.doctor
            return doctor.status == 'approved'
        except Doctor.DoesNotExist:
            return False