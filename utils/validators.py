import re

class Validators:
    @staticmethod
    def validate_email(email):
        """Validate if the email is in a valid format."""
        if not email:
            return True
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, email))

    @staticmethod
    def validate_mobile(mobile):
        """Validate if the mobile number is in a valid format (digits, spaces, hyphens, plus sign, length between 7 and 15)."""
        if not mobile:
            return False
        clean_mobile = re.sub(r'[\s\-()+]', '', mobile)
        if not clean_mobile.isdigit():
            return False
        return 7 <= len(clean_mobile) <= 15

    @staticmethod
    def validate_name(name):
        """Validate if the name is non-empty and contains only alphabet characters, spaces, and dots."""
        if not name or len(name.strip()) < 2:
            return False
        name_regex = r'^[a-zA-Z\s\.\'\-]+$'
        return bool(re.match(name_regex, name))

    @staticmethod
    def validate_required(value):
        """Validate if a required field is not empty."""
        if value is None:
            return False
        if isinstance(value, str):
            return len(value.strip()) > 0
        return True
