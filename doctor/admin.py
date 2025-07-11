from django.contrib import admin
from .models import Doctor, DoctorProfile, Appointment, Consent, PatientHistory, AccessLog, MedicalNote, PrescriptionUpload

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'specialty', 'status', 'created_at')
    list_filter = ('status', 'specialty')
    search_fields = ('name', 'email', 'reg_id')

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'bio', 'fees', 'created_at')
    search_fields = ('doctor__name', 'bio')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient_id', 'date', 'time', 'mode', 'status', 'created_at')
    list_filter = ('status', 'mode', 'date')
    search_fields = ('doctor__name', 'patient_id')

@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient_id', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('doctor__name', 'patient_id')

@admin.register(PatientHistory)
class PatientHistoryAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'created_at', 'updated_at')
    search_fields = ('patient_id',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'patient_id', 'action', 'accessed_at')
    list_filter = ('action', 'accessed_at')
    search_fields = ('user__username', 'patient_id')
    readonly_fields = ('accessed_at',)

@admin.register(MedicalNote)
class MedicalNoteAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('appointment__id', 'notes')
    readonly_fields = ('created_at',)

@admin.register(PrescriptionUpload)
class PrescriptionUploadAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient_id', 'appointment', 'file', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('doctor__name', 'patient_id', 'appointment__id')
    readonly_fields = ('timestamp',)