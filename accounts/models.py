from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils import timezone

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True
    

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom User model with email as the unique identifier."""
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    # Mise à jour du validateur pour accepter les formats internationaux E.164
    phone_regex = RegexValidator(
        regex=r'^\+[1-9]\d{1,14}$',
        message="Le numéro de téléphone doit être au format international (ex: +33612345678)."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, unique=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    pin_code = models.CharField(max_length=4, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    # Préférences utilisateur
    language = models.CharField(max_length=10, default='fr')
    dark_mode = models.BooleanField(default=False)
    enable_notifications = models.BooleanField(default=True)
    
    # Champs pour le parrainage
    referral_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    last_activity = models.DateTimeField(default=timezone.now)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number', 'first_name', 'last_name']
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()
    
    def get_initials(self):
        """Return user initials for display."""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        elif self.last_name:
            return self.last_name[0].upper()
        else:
            return self.email[0].upper() if self.email else "U"
    
    def save(self, *args, **kwargs):
        # Générer un code de parrainage s'il n'existe pas
        if not self.referral_code and self.pk:
            import random
            import string
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.referral_code = code
        super().save(*args, **kwargs)
    
    def is_inactive_for_long(self, days=3):
        """Vérifie si l'utilisateur est inactif depuis plus de X jours."""
        if not self.last_activity:
            return False
        inactive_threshold = timezone.now() - timezone.timedelta(days=days)
        return self.last_activity < inactive_threshold


class UserVerification(models.Model):
    """Model to store verification codes for user phone numbers."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    sms_sid = models.CharField(max_length=255, null=True, blank=True)  # Store Twilio SMS SID
    
    def __str__(self):
        return f"Verification for {self.user.email} - {self.code}"
    
    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()


class UserSecurityQuestion(models.Model):
    """Security questions for account recovery."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_questions')
    question = models.CharField(max_length=255)
    answer = models.CharField(max_length=255)
    
    def __str__(self):
        return f"Security question for {self.user.email}"


class PhoneNumber(models.Model):
    """Model to store verified phone numbers."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_numbers')
    phone_number = models.CharField(max_length=17, unique=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.phone_number} ({self.user.email})"




# opay_fintech/accounts/models.py

class UserActivity(models.Model):
    """Model to track user activities."""
    
    ACTIVITY_TYPES = (
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('profile_update', 'Modification du profil'),
        ('password_change', 'Changement de mot de passe'),
        ('pin_change', 'Changement de code PIN'),
        ('transaction', 'Transaction'),
        ('security_update', 'Mise à jour de sécurité'),
        ('other', 'Autre activité'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Activité utilisateur'
        verbose_name_plural = 'Activités utilisateurs'
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.user.email} - {self.timestamp}"



from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('transfer_sent', 'Transfert envoyé'),
        ('transfer_received', 'Transfert reçu'),
        ('deposit', 'Dépôt'),
        ('withdrawal', 'Retrait'),
        ('profile_update', 'Profil mis à jour'),
        ('account_security', 'Sécurité du compte'),
        ('bill_payment', 'Paiement de facture'),
        ('system', 'Notification système'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    icon = models.CharField(max_length=50, default='bell')  # Classe FontAwesome
    link = models.CharField(max_length=255, blank=True, null=True)  # Lien vers la ressource concernée
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        self.read = True
        self.save()
