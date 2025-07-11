from django.core.exceptions import ValidationError
import os

def validate_document_file(file):
    # Define allowed file extensions
    allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg']
    max_size_mb = 5  # Maximum file size in MB
    max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes

    # Check file extension
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Invalid file type. Allowed types are: {', '.join(allowed_extensions)}"
        )

    # Check file size
    if file.size > max_size_bytes:
        raise ValidationError(
            f"File size exceeds {max_size_mb}MB limit."
        )