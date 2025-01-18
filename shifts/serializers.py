from rest_framework import serializers
from .models import Shift, User, Location, WorkerProfile, Availability, Notification

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class ShiftSerializer(serializers.ModelSerializer):
    worker = UserSerializer()
    location = serializers.StringRelatedField()

    class Meta:
        model = Shift
        fields = ['id', 'date', 'start_time', 'end_time', 'location', 'is_completed', 'worker']

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'postcode', 'latitude', 'longitude', 'weekday_rate', 'saturday_rate', 'sunday_rate', 'sleep_in_rate']

class WorkerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = WorkerProfile
        fields = ['id', 'user', 'signature']

class AvailabilitySerializer(serializers.ModelSerializer):
    worker = UserSerializer()

    class Meta:
        model = Availability
        fields = ['id', 'worker', 'date', 'is_available']

class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Notification
        fields = ['id', 'user', 'content', 'timestamp', 'read']