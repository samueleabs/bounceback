# shifts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    is_worker = models.BooleanField(default=False)
    webpush_subscription = models.JSONField(blank=True, null=True)

class WorkerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    signature = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    # Additional fields for worker profile

class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    postcode = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    weekday_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saturday_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sunday_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sleep_in_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.name
class Shift(models.Model):
    worker = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    sleep_in = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    signature = models.TextField(blank=True, null=True)  # Store as data URL or file path
    signed_by = models.CharField(max_length=255, blank=True, null=True)  # Name of the person signing the timesheet
    reference = models.CharField(max_length=255, blank=True, null=True)  # Reference number for the shift
    timesheet_generated = models.BooleanField(default=False)  # Field to mark timesheet generation

    def __str__(self):
        return f"{self.worker.username} - {self.date} - {self.location.name}"

class Availability(models.Model):
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="availability")
    date = models.DateField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.worker.username} - {self.date}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user} at {self.timestamp}"


class UserToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)