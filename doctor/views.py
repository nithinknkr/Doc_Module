from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from .serializers import (
    DoctorOnboardingSerializer, DoctorAdminSerializer,
    DoctorProfileSerializer, DoctorPublicPreviewSerializer,
    AppointmentSerializer, ConsentSerializer, PatientHistorySerializer,
    PrescriptionUploadSerializer
)
from .models import Doctor, DoctorProfile, Appointment, Consent, PatientHistory, AccessLog, PrescriptionUpload
from .notifications import send_notification
from .permissions import IsDoctor
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.utils import timezone
import uuid
import os
from django.core.files.storage import default_storage

class DoctorOnboardingView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DoctorOnboardingSerializer(data=request.data)
        if serializer.is_valid():
            doctor = serializer.save()
            return Response({
                'message': 'Doctor onboarding submitted successfully.',
                'doctor_id': doctor.id,
                'status': 'pending'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorAdminView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        doctors = Doctor.objects.filter(status='pending')
        serializer = DoctorAdminSerializer(doctors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        try:
            doctor = Doctor.objects.get(pk=pk, status='pending')
        except Doctor.DoesNotExist:
            return Response({
                'error': 'Doctor not found or not pending.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorAdminSerializer(doctor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            send_notification(doctor, serializer.data['status'])
            return Response({
                'message': f'Doctor {doctor.name} status updated to {serializer.data["status"]}.'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorProfileView(APIView):
    permission_classes = [IsDoctor]

    def put(self, request):
        try:
            doctor = request.user.doctor
            if doctor.status != 'approved':
                return Response({
                    'error': 'Only approved doctors can update their profile.'
                }, status=status.HTTP_403_FORBIDDEN)
            profile = doctor.profile
        except DoctorProfile.DoesNotExist:
            profile = DoctorProfile.objects.create(doctor=doctor)
        except Doctor.DoesNotExist:
            return Response({
                'error': 'Doctor not found.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = DoctorProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorPublicPreviewView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        if pk:
            try:
                doctor = Doctor.objects.get(pk=pk)
                serializer = DoctorPublicPreviewSerializer(doctor)
                data = serializer.data
                if not data:
                    return Response({
                        'error': 'Doctor not found or not approved.'
                    }, status=status.HTTP_404_NOT_FOUND)
                return Response(data, status=status.HTTP_200_OK)
            except Doctor.DoesNotExist:
                return Response({
                    'error': 'Doctor not found.'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            doctors = Doctor.objects.all()
            serializer = DoctorPublicPreviewSerializer(doctors, many=True)
            data = [item for item in serializer.data if item]
            return Response(data, status=status.HTTP_200_OK)

class AppointmentViewSet(ViewSet):
    permission_classes = [IsDoctor]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['date', 'time', 'status']
    ordering_fields = ['date', 'time']
    ordering = ['date', 'time']

    def list(self, request):
        doctor = request.user.doctor
        if doctor.status != 'approved':
            return Response({
                'error': 'Only approved doctors can view appointments.'
            }, status=status.HTTP_403_FORBIDDEN)
        queryset = Appointment.objects.filter(doctor=doctor)
        specialty = request.query_params.get('specialty')
        if specialty:
            queryset = queryset.filter(doctor__specialty=specialty)
        serializer = AppointmentSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        doctor = request.user.doctor
        if doctor.status != 'approved':
            return Response({
                'error': 'Only approved doctors can manage appointments.'
            }, status=status.HTTP_403_FORBIDDEN)
        data = request.data.copy()
        data['doctor_id'] = doctor.id
        serializer = AppointmentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        doctor = request.user.doctor
        if doctor.status != 'approved':
            return Response({
                'error': 'Only approved doctors can reschedule appointments.'
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            appointment = Appointment.objects.get(pk=pk, doctor=doctor)
        except Appointment.DoesNotExist:
            return Response({
                'error': 'Appointment not found or not associated with this doctor.'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = AppointmentSerializer(appointment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        doctor = request.user.doctor
        if doctor.status != 'approved':
            return Response({
                'error': 'Only approved doctors can mark appointments as no-show.'
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            appointment = Appointment.objects.get(pk=pk, doctor=doctor)
        except Appointment.DoesNotExist:
            return Response({
                'error': 'Appointment not found or not associated with this doctor.'
            }, status=status.HTTP_404_NOT_FOUND)
        if 'status' in request.data and request.data['status'] == 'no-show':
            serializer = AppointmentSerializer(appointment, data={'status': 'no-show'}, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'error': 'Only status update to no-show is allowed.'
        }, status=status.HTTP_400_BAD_REQUEST)

class ConsentViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        try:
            doctor = request.user.doctor
            if doctor.status != 'approved':
                return Response({
                    'error': 'Only approved doctors can request consent.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Doctor.DoesNotExist:
            return Response({
                'error': 'User is not a doctor.'
            }, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data['doctor_id'] = doctor.id
        serializer = ConsentSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            consent = serializer.save()
            print(f"Notification: Consent request sent to patient {consent.patient_id} from {doctor.name}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        try:
            consent = Consent.objects.get(pk=pk)
        except Consent.DoesNotExist:
            return Response({
                'error': 'Consent request not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_authenticated:
            return Response({
                'error': 'Authentication required to approve/deny consent.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        serializer = ConsentSerializer(consent, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            print(f"Notification: Consent {consent.status} for patient {consent.patient_id} by {consent.doctor.name}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        try:
            doctor = request.user.doctor
            if doctor.status != 'approved':
                return Response({
                    'error': 'Only approved doctors can view consents.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Doctor.DoesNotExist:
            return Response({
                'error': 'User is not a doctor.'
            }, status=status.HTTP_403_FORBIDDEN)

        consents = Consent.objects.filter(doctor=doctor)
        serializer = ConsentSerializer(consents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PatientHistoryView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request, patient_id):
        try:
            doctor = request.user.doctor
            if doctor.status != 'approved':
                return Response({
                    'error': 'Only approved doctors can view patient history.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Doctor.DoesNotExist:
            return Response({
                'error': 'User is not a doctor.'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            consent = Consent.objects.get(doctor=doctor, patient_id=patient_id, status='granted')
        except Consent.DoesNotExist:
            return Response({
                'error': 'No granted consent found for this patient.'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            history = PatientHistory.objects.get(patient_id=patient_id)
        except PatientHistory.DoesNotExist:
            return Response({
                'error': 'Patient history not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        AccessLog.objects.create(
            user=request.user,
            patient_id=patient_id,
            action='viewed'
        )

        serializer = PatientHistorySerializer(history)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PrescriptionUploadView(APIView):
    permission_classes = [IsDoctor]

    def post(self, request):
        try:
            doctor = request.user.doctor
            if doctor.status != 'approved':
                return Response({
                    'error': 'Only approved doctors can upload prescriptions.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Doctor.DoesNotExist:
            return Response({
                'error': 'User is not a doctor.'
            }, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data['doctor_id'] = doctor.id

        # Generate unique filename
        file = request.FILES.get('file')
        if file:
            ext = os.path.splitext(file.name)[1]
            unique_filename = f"{uuid.uuid4()}{ext}"
            data['file'] = file
            data['file'].name = f"prescriptions/{doctor.id}/{unique_filename}"

        serializer = PrescriptionUploadSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Prescription uploaded successfully.',
                'prescription_id': serializer.data['id'],
                'file_url': serializer.data['file']
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PrescriptionViewSet(ViewSet):
    permission_classes = [IsDoctor]

    def retrieve(self, request, pk=None):
        try:
            doctor = request.user.doctor
            if doctor.status != 'approved':
                return Response({
                    'error': 'Only approved doctors can view prescriptions.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Doctor.DoesNotExist:
            return Response({
                'error': 'User is not a doctor.'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            prescription = PrescriptionUpload.objects.get(pk=pk, doctor=doctor)
        except PrescriptionUpload.DoesNotExist:
            return Response({
                'error': 'Prescription not found or not associated with this doctor.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PrescriptionUploadSerializer(prescription)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        try:
            doctor = request.user.doctor
            if doctor.status != 'approved':
                return Response({
                    'error': 'Only approved doctors can delete prescriptions.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Doctor.DoesNotExist:
            return Response({
                'error': 'User is not a doctor.'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            prescription = PrescriptionUpload.objects.get(pk=pk, doctor=doctor)
        except PrescriptionUpload.DoesNotExist:
            return Response({
                'error': 'Prescription not found or not associated with this doctor.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Delete the file from storage
        if default_storage.exists(prescription.file.path):
            default_storage.delete(prescription.file.path)

        prescription.delete()
        return Response({
            'message': 'Prescription deleted successfully.'
        }, status=status.HTTP_204_NO_CONTENT)