from django.db import models
from django.contrib.auth.models import User
from .validators import validate_document_file
import uuid

class Doctor(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor')
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, unique=True)
    specialty = models.CharField(max_length=100)
    clinic_address = models.TextField(blank=True, null=True)
    govt_id = models.FileField(upload_to='doctor_documents/govt_id/', validators=[validate_document_file])
    medical_certificate = models.FileField(upload_to='doctor_documents/medical_certificate/', validators=[validate_document_file])
    reg_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} ({self.specialty})"

class DoctorProfile(models.Model):
    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    specialties = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    clinic_timings = models.JSONField(default=dict, blank=True)
    languages = models.JSONField(default=list, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.doctor.name}"

class Appointment(models.Model):
    MODE_CHOICES = [
        ('online', 'Online'),
        ('in-person', 'In-Person'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('no-show', 'No-Show'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    patient_id = models.UUIDField(default=uuid.uuid4, editable=False)
    date = models.DateField()
    time = models.TimeField()
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='online')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Appointment with {self.doctor.name} on {self.date} at {self.time}"

class Consent(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('granted', 'Granted'),
        ('denied', 'Denied'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='consents')
    patient_id = models.UUIDField(default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['patient_id']),
        ]
        unique_together = ['doctor', 'patient_id']

    def __str__(self):
        return f"Consent for {self.doctor.name} by Patient {self.patient_id} ({self.status})"

class PatientHistory(models.Model):
    patient_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    reports = models.JSONField(default=list, blank=True)
    vitals = models.JSONField(default=dict, blank=True)
    prescriptions = models.JSONField(default=list, blank=True)
    visits = models.JSONField(default=list, blank=True)
    flags = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['patient_id']),
        ]

    def __str__(self):
        return f"History for Patient {self.patient_id}"

class AccessLog(models.Model):
    ACTION_CHOICES = [
        ('viewed', 'Viewed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_logs')
    patient_id = models.UUIDField()
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default='viewed')
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['accessed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} {self.action} history for Patient {self.patient_id} at {self.accessed_at}"

class MedicalNote(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='medical_notes')
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['appointment']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Note for Appointment {self.appointment.id} at {self.created_at}"

class PrescriptionUpload(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescriptions')
    patient_id = models.UUIDField(default=uuid.uuid4, editable=False)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions')
    file = models.FileField(upload_to='prescriptions/%Y/%m/%d/', validators=[validate_document_file])
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"Prescription for Patient {self.patient_id} by {self.doctor.name} at {self.timestamp}"