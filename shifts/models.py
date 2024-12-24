# shifts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    is_worker = models.BooleanField(default=False)

class WorkerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    signature = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    # Additional fields for worker profile

class Location(models.Model):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.TextField()
    postcode = models.CharField(max_length=20)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

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
    timesheet_generated = models.BooleanField(default=False)  # Field to mark timesheet generation

    def __str__(self):
        return f"{self.worker.username} - {self.date} - {self.location.name}"

class Availability(models.Model):
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="availability")
    date = models.DateField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.worker.username} - {self.date}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)