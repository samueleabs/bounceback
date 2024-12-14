# shifts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    is_worker = models.BooleanField(default=False)

class WorkerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Additional fields for worker profile

class Location(models.Model):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Shift(models.Model):
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shifts")
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_completed = models.BooleanField(default=False)
    sleep_in = models.BooleanField(default=False)
    signature = models.TextField(blank=True, null=True)  # Add this field to store the signature

class Availability(models.Model):
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="availability")
    day = models.CharField(max_length=9, choices=[("Monday", "Monday"), ("Tuesday", "Tuesday"), ("Wednesday", "Wednesday"), ("Thursday", "Thursday"), ("Friday", "Friday"), ("Saturday", "Saturday"), ("Sunday", "Sunday")])
    is_available = models.BooleanField(default=True)

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)