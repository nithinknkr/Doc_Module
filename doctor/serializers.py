from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Doctor, DoctorProfile, Appointment, Consent, PatientHistory, PrescriptionUpload 
from django.utils import timezone
import uuid

class DoctorOnboardingSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    email = serializers.EmailField()

    class Meta:
        model = Doctor
        fields = [
            'username', 'password', 'name', 'email', 'mobile', 'specialty',
            'clinic_address', 'govt_id', 'medical_certificate', 'reg_id'
        ]

    def create(self, validated_data):
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        email = validated_data.pop('email')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        doctor = Doctor.objects.create(
            user=user,
            email=email,
            **validated_data,
            status='pending'
        )
        return doctor

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

class DoctorAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'name', 'email', 'specialty', 'reg_id', 'govt_id', 'medical_certificate', 'status']
        read_only_fields = ['id', 'name', 'email', 'specialty', 'reg_id', 'govt_id', 'medical_certificate']

    def validate_status(self, value):
        if value not in ['approved', 'rejected']:
            raise serializers.ValidationError("Status must be 'approved' or 'rejected'.")
        return value

class DoctorProfileSerializer(serializers.ModelSerializer):
    completeness_percentage = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = [
            'bio', 'specialties', 'certifications', 'clinic_timings',
            'languages', 'fees', 'completeness_percentage'
        ]

    def validate_specialties(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Specialties must be a list.")
        return value

    def validate_languages(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Languages must be a list.")
        return value

    def validate_certifications(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Certifications must be a list.")
        for cert in value:
            if not isinstance(cert, dict) or 'name' not in cert or 'date' not in cert:
                raise serializers.ValidationError("Each certification must be a dict with 'name' and 'date'.")
        return value

    def validate_clinic_timings(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Clinic timings must be a dictionary.")
        return value

    def get_completeness_percentage(self, obj):
        fields = ['bio', 'specialties', 'certifications', 'clinic_timings', 'languages', 'fees']
        total_fields = len(fields)
        filled_fields = 0

        for field in fields:
            value = getattr(obj, field)
            if field == 'fees':
                if value is not None:
                    filled_fields += 1
            elif field in ['specialties', 'certifications', 'languages']:
                if isinstance(value, list) and len(value) > 0:
                    filled_fields += 1
            elif field == 'clinic_timings':
                if isinstance(value, dict) and len(value) > 0:
                    filled_fields += 1
            elif value:
                filled_fields += 1

        percentage = (filled_fields / total_fields) * 100 if total_fields > 0 else 0
        return round(percentage, 2)

class DoctorPublicPreviewSerializer(serializers.ModelSerializer):
    profile = DoctorProfileSerializer(read_only=True)
    specialty = serializers.CharField()

    class Meta:
        model = Doctor
        fields = ['id', 'name', 'specialty', 'clinic_address', 'profile']

    def to_representation(self, instance):
        if instance.status != 'approved':
            return {}
        return super().to_representation(instance)

class AppointmentSerializer(serializers.ModelSerializer):
    doctor_id = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all(), source='doctor')
    rejection_reason = serializers.CharField(max_length=255, write_only=True, required=False)

    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor_id', 'patient_id', 'date', 'time', 'mode', 'status',
            'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'patient_id', 'created_at', 'updated_at']

    def validate(self, data):
        if 'date' in data:
            if data['date'] < timezone.now().date():
                raise serializers.ValidationError("Appointment date cannot be in the past.")
        if data.get('status') == 'rejected' and not data.get('rejection_reason'):
            raise serializers.ValidationError("Rejection reason is required when status is 'rejected'.")
        return data

    def update(self, instance, validated_data):
        if validated_data.get('rejection_reason'):
            instance.rejection_reason = validated_data.pop('rejection_reason')
        return super().update(instance, validated_data)

class ConsentSerializer(serializers.ModelSerializer):
    doctor_id = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all(), source='doctor')
    patient_id = serializers.UUIDField(required=True)

    class Meta:
        model = Consent
        fields = ['id', 'doctor_id', 'patient_id', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_patient_id(self, value):
        try:
            uuid.UUID(str(value))
        except ValueError:
            raise serializers.ValidationError("Patient ID must be a valid UUID.")
        return value

    def validate(self, data):
        doctor = data.get('doctor')
        patient_id = data.get('patient_id')
        request = self.context.get('request')
        user = request.user if request else None

        if self.instance is None and Consent.objects.filter(doctor=doctor, patient_id=patient_id).exists():
            raise serializers.ValidationError("Consent request for this patient and doctor already exists.")

        if self.instance and data.get('status'):
            if self.instance.status == 'granted' and data['status'] in ['pending', 'denied']:
                raise serializers.ValidationError("Cannot change granted consent to pending or denied.")
            if self.instance.status == 'denied' and data['status'] == 'pending':
                raise serializers.ValidationError("Cannot change denied consent back to pending.")

        return data

class PatientHistorySerializer(serializers.ModelSerializer):
    summary = serializers.SerializerMethodField()

    class Meta:
        model = PatientHistory
        fields = ['patient_id', 'reports', 'vitals', 'prescriptions', 'visits', 'flags', 'summary', 'created_at', 'updated_at']
        read_only_fields = ['patient_id', 'created_at', 'updated_at']

    def get_summary(self, obj):
        summary = {
            'report_count': len(obj.reports),
            'vital_count': len(obj.vitals),
            'prescription_count': len(obj.prescriptions),
            'visit_count': len(obj.visits),
            'critical_alerts': 0
        }
        if isinstance(obj.flags, dict) and 'conditions' in obj.flags:
            critical_conditions = ['diabetes', 'hypertension', 'cancer']  
            summary['critical_alerts'] = sum(
                1 for condition in obj.flags.get('conditions', [])
                if condition.lower() in critical_conditions
            )
        return summary
    
class PrescriptionUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionUpload
        fields = ['id', 'doctor', 'patient_id', 'appointment', 'file', 'timestamp']
        read_only_fields = ['doctor', 'timestamp']

    def validate(self, data):
        appointment = data.get('appointment')
        doctor = self.context['request'].user.doctor

        if appointment.doctor != doctor:
            raise serializers.ValidationError({"appointment": "Appointment does not belong to this doctor."})

        if data.get('patient_id') != appointment.patient_id:
            raise serializers.ValidationError({"patient_id": "Patient ID does not match the appointment's patient ID."})

        return data