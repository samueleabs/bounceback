# shifts/admin.py
from django.contrib import admin
from .models import User, WorkerProfile, Location, Shift, Availability

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_admin', 'is_worker')
    list_filter = ('is_admin', 'is_worker')
    search_fields = ('username', 'email')

class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__email')

class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate')
    search_fields = ('name',)

class ShiftAdmin(admin.ModelAdmin):
    list_display = ('worker', 'location', 'date', 'start_time', 'end_time', 'is_completed', 'sleep_in')
    list_filter = ('is_completed', 'sleep_in', 'location')
    search_fields = ('worker__username', 'location__name')

class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('worker', 'date', 'is_available')
    list_filter = ('date', 'is_available')



admin.site.register(User, UserAdmin)
admin.site.register(WorkerProfile, WorkerProfileAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(Availability, AvailabilityAdmin)
