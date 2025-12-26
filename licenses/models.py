from django.db import models
from django.utils import timezone
import datetime

class Client(models.Model):
    name = models.CharField(max_length=100)
    hardware_id = models.CharField(max_length=200)
    secret_key = models.TextField()
    validity_seconds = models.IntegerField(default=31536000) 
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    @property
    def expiry_date(self):
        # Calculate the exact expiration time
        return self.created_at + datetime.timedelta(seconds=self.validity_seconds)

    @property
    def is_active(self):
        # Returns True if current time is BEFORE expiry date
        return timezone.now() < self.expiry_date

    @property
    def time_remaining(self):
        """
        Returns a nice string string for display only.
        """
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