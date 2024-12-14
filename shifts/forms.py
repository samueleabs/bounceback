# shifts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Shift, Availability, Message

class WorkerSignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

class ShiftForm(forms.ModelForm):
    date = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker'}))
    start_time = forms.TimeField(widget=forms.TextInput(attrs={'class': 'timepicker'}))
    end_time = forms.TimeField(widget=forms.TextInput(attrs={'class': 'timepicker'}))

    class Meta:
        model = Shift
        fields = ['worker', 'location', 'date', 'start_time', 'end_time', 'sleep_in', 'signature']

class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ['worker', 'day', 'is_available']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'content']

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']