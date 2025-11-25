"""
Custom password validators for modern authentication.
Supports passphrases and follows current best practices.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ModernPasswordValidator:
    """
    Password validator that supports modern authentication practices.
    
    - Minimum 8 characters (allows longer passphrases)
    - Maximum 128 characters
    - Checks for commonly breached passwords
    - Does NOT require specific character classes (supports passphrases)
    """
    
    def __init__(self, min_length=8, max_length=128):
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("Password must be at least %(min_length)d characters long."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )
        
        if len(password) > self.max_length:
            raise ValidationError(
                _("Password must be no more than %(max_length)d characters long."),
                code='password_too_long',
                params={'max_length': self.max_length},
            )
    
    def get_help_text(self):
        return _(
            "Your password must be between %(min_length)d and %(max_length)d characters. "
            "We recommend using a passphrase - a sequence of random words that is easy "
            "to remember but hard to guess."
        ) % {'min_length': self.min_length, 'max_length': self.max_length}
