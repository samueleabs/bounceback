from django.db import models

class Worker(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Shift(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name="shifts")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_completed = models.BooleanField(default=False)  # For sign-off

    def __str__(self):
        return f"{self.worker.name} - {self.date}"

class Availability(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name="availability")
    day = models.CharField(max_length=9, choices=[("Monday", "Monday"), ("Tuesday", "Tuesday"), ("Wednesday", "Wednesday"), ("Thursday", "Thursday"), ("Friday", "Friday"), ("Saturday", "Saturday"), ("Sunday", "Sunday")])
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.worker.name} - {self.day} ({'Available' if self.is_available else 'Not Available'})"