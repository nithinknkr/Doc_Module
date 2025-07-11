def send_notification(doctor, status):
    """
    this is only for status of doctor wether it got approved or regected by admin.
    Right now the notification will be showing the console only but it should be implemented in future to send the notifications. through mail(registred mail of doctor) or sms(registered phonenumber of doctor)."""
    
    message = f"Notification: Doctor {doctor.name} ({doctor.email}) status updated to {status}."
    print(message)  # Log to console
    # Future: Replace with email/SMS service integration (e.g., SendGrid, Twilio)