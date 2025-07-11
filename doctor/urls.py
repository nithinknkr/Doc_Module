from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DoctorOnboardingView, DoctorAdminView, DoctorProfileView,
    DoctorPublicPreviewView, AppointmentViewSet, ConsentViewSet,
    PatientHistoryView, PrescriptionUploadView, PrescriptionViewSet
)

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'consents', ConsentViewSet, basename='consent')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')

urlpatterns = [
    path('onboard/', DoctorOnboardingView.as_view(), name='doctor-onboarding'),
    path('admin/<int:pk>/', DoctorAdminView.as_view(), name='doctor-admin'),
    path('admin/', DoctorAdminView.as_view(), name='doctor-admin-list'),
    path('profile/', DoctorProfileView.as_view(), name='doctor-profile'),
    path('public/<int:pk>/', DoctorPublicPreviewView.as_view(), name='doctor-public-preview'),
    path('public/', DoctorPublicPreviewView.as_view(), name='doctor-public-preview-list'),
    path('history/<uuid:patient_id>/', PatientHistoryView.as_view(), name='patient-history'),
    path('prescriptions/upload/', PrescriptionUploadView.as_view(), name='prescription-upload'),
    path('', include(router.urls)),
]