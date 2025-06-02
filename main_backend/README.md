CONFIDENTIAL NOTICE – LiveSure Project
This task document outlines the development plan for core features of LiveSure, including proprietary AI workflows, healthcare coordination logic, and modular system architecture. The information contained herein is considered strictly confidential.
All source code, designs, APIs, and documentation produced as part of this work are the intellectual property of LiveSure and contribute directly to the core innovation of the platform.
Any unauthorized use, reproduction, distribution, or disclosure of this material, in whole or in part, is strictly prohibited and may be subject to legal action under applicable intellectual property laws.
All rights reserved by LiveSure.




your task  - Asmi Shetty

1. Doctor Onboarding
Goal: Register and verify only licensed practitioners.

🔧 Backend Tasks:
Create Doctor model with fields: name, email, mobile, specialty, clinic address (optional), and document uploads (Govt ID, medical certificate, reg ID).

Implement document validation logic (file type, size, format).

Create serializer & API view for onboarding form.

Add status field (pending, approved, rejected) with email/SMS notifications on state change.

Set up admin moderation API for approval workflow.

Optional: Progress tracking during signup (handled frontend, but API should return steps completed).

2. Profile Management
Goal: Allow doctors to manage public/clinical-facing profiles.

🔧 Backend Tasks:
Extend the Doctor model or create a linked DoctorProfile model.

API to update: bio, specialties, certifications (with dates), clinic timings, languages, fees.

Add profile completeness calculator logic in serializer (e.g., % of fields filled).

Endpoint for “Preview as Patient” (return sanitized public view).

3. Appointment Management
Goal: View, filter, and manage appointments.

🔧 Backend Tasks:
Build Appointment model with fields: doctor, patient, date, time, mode (online/in-person), and status.

Views to:

Accept/Reject with reason

Reschedule

Mark as no-show

Filter by time slot or specialty

Create calendar-style API (grouped by today, upcoming, etc.)

4. Patient History Access
Goal: Controlled access to medical history with consent.

🔧 Backend Tasks:
Consent model with fields: doctor, patient, status (pending, granted, denied), timestamps.

API:

Request access (triggers notification to patient)

Approve/deny endpoint (for patient side)

Data retrieval only if access is granted

Retrieve patient data: past reports, vitals, prescriptions, visits.

Add quick flags (e.g., allergies, conditions) to summaries.

Create summary endpoint returning meta: “10 reports, 3 critical alerts, 2 ongoing conditions”.




Doctor Module – 5-Day Sprint Plan (Django REST)
💡 Assumption: 1–2 developers, full-day sprint cycle (6–8 hrs/day). Adjust per bandwidth.

🔹 Day 1 – Onboarding & Basic Models
Goals:

Set up core doctor schema and registration flow

Tasks:

 Create Doctor model with all necessary fields (name, mobile, reg ID, etc.)

 Create API endpoint for doctor onboarding (step-by-step fields)

 Implement document upload (medical cert, ID proof)

 Add status field (pending, approved, rejected)

 Write admin-side approval API

 Setup role-based access permissions (IsDoctor, IsAdmin)

 Test onboarding API using Postman

🔹 Day 2 – Profile Management APIs
Goals:

Enable doctors to manage their profile after approval

Tasks:

 Create DoctorProfile model or extend Doctor model

 API to update profile: bio, clinic timings, specialties, fees

 Implement serializer logic for profile completeness tracking

 API for “public preview” of profile (sanitized data)

 Add logic to restrict access until onboarding is approved

 Unit test profile update + preview endpoints

🔹 Day 3 – Appointments Handling
Goals:

Enable doctors to manage appointments effectively

Tasks:

 Create Appointment model (patient, doctor, time, mode, status)

 Create viewset to accept/reject appointments with reasons

 Add calendar-style grouped API (today, upcoming, past)

 Allow doctors to reschedule appointments

 Create serializer logic for grouped appointment view

 Write test cases for all appointment actions

🔹 Day 4 – Patient History & Consent Flow
Goals:

Securely access patient records with proper consent

Tasks:

 Create ConsentRequest model (doctor, patient, status, timestamps)

 API to request access from doctor side

 API to approve/deny consent from patient side

 Fetch patient history only when access is granted

 Endpoint for “patient summary” (vitals, alerts, reports count)

 Log every access for auditing

 Write access control test cases


Day 5 – Medical Notes & Prescription Upload System
Goal: Allow doctors to document visits and upload prescription files securely

🔧 Updated Tasks:
 Create MedicalNote model (linked to Appointment, contains consultation notes)

 Create PrescriptionUpload model:

Fields: doctor, patient, appointment, file (FileField or ImageField), timestamp

Accepts PDF or image formats (limit size for optimization)

 API to:

Upload prescription file

Retrieve/download prescription per appointment

Delete/update (if needed, with restrictions)

 Save files securely in MEDIA_ROOT with proper subfoldering (/prescriptions/<doctor_id>/)

 Optional: Add watermark or document metadata (e.g., “Generated via LiveSure”)

 Add notification trigger (SMS/email/push placeholder)

 Test file upload/download API flow

 Validate file type, extension, size on server side
 
