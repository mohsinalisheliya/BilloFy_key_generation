from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

# --- YOUR EXISTING CLIENT MODEL ---
class Client(models.Model):
    name = models.CharField(max_length=100)
    hardware_id = models.CharField(max_length=200,unique=True)
    secret_key = models.TextField()
    validity_seconds = models.IntegerField(default=31536000) 
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def expiry_date(self):
        import datetime
        return self.created_at + datetime.timedelta(seconds=self.validity_seconds)

    @property
    def is_active(self):
        return timezone.now() < self.expiry_date

    @property
    def time_remaining(self):
        if not self.is_active:
            return "Expired"
        delta = self.expiry_date - timezone.now()
        if delta.days >= 1:
            return f"{delta.days} Days"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} Hours"
        else:
            minutes = delta.seconds // 60
            return f"{minutes} Mins"

    def __str__(self):
        return self.name

# --- NEW SEPARATE LOGIN MODEL ---
class Login(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=128)

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def __str__(self):
        return self.username

# --- SITE SETTINGS MODEL ---
class SiteSetting(models.Model):
    """
    Singleton model to store site branding configuration.
    Only one record should exist in the database.
    """
    project_name = models.CharField(max_length=100, default='BilloFy Admin', help_text='Full project name')
    project_name_short = models.CharField(max_length=50, default='BilloFy', help_text='Short project name')
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, help_text='Upload a logo image')
    logo_path = models.CharField(max_length=255, default='images/billofy_key.png', help_text='Path to logo file in static folder (fallback)')
    primary_color = models.CharField(max_length=50, default='red', help_text='Primary brand color')
    updated_at = models.DateTimeField(auto_now=True)
    
    github_token = models.CharField(max_length=255, blank=True, null=True,
        help_text="Fine-grained PAT for pushing releases to GitHub")
    github_repo = models.CharField(max_length=255, blank=True, null=True,
        default="mohsinalisheliya/billofy-releases",
        help_text="Format: username/repo-name")
    github_token_expiry = models.DateField(blank=True, null=True,
        help_text="Jab tak token valid hai — dashboard pe warning ke liye")


    class Meta:
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of the singleton instance"""
        pass
    
    @classmethod
    def load(cls):
        """Load the singleton instance, create if doesn't exist"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def get_logo_url(self):
        """Get the logo URL - uploaded file takes precedence over static path"""
        if self.logo:
            return self.logo.url
        return f'/static/{self.logo_path}'
    
    def __str__(self):
        return f"Site Settings - {self.project_name}"



# --- SOFTWARE UPDATE MODEL ---
def update_file_path(instance, filename):
   
    import os

    return f'updates/{filename}'

class SoftwareUpdate(models.Model):
    version = models.CharField(max_length=20, unique=True, help_text="e.g. 1.0.1")
    title = models.CharField(max_length=100, default="New Update")
    description = models.TextField(blank=True)
    download_url = models.URLField(max_length=500, blank=True, null=True,help_text="GitHub Release asset download URL")
    update_file = models.FileField(upload_to=update_file_path)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    UPDATE_TYPES = [
        ('optional', 'Optional'),
        ('recommended', 'Recommended'),
        ('critical', 'Critical'),
    ]
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPES, default='optional')
    def __str__(self):
        return f"v{self.version}: {self.title}"