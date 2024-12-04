from django.contrib import admin
from .models import Worker, Shift, Availability

admin.site.register(Worker)
admin.site.register(Shift)
admin.site.register(Availability)
