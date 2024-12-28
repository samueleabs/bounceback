# shifts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *

class WorkerSignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password1', 'password2']

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']

class ShiftForm(forms.ModelForm):
    date = forms.DateField(widget=forms.TextInput(attrs={'class': 'form-control datepicker'}))
    start_time = forms.TimeField(widget=forms.TextInput(attrs={'class': 'form-control timepicker'}))
    end_time = forms.TimeField(widget=forms.TextInput(attrs={'class': 'form-control timepicker'}))

    class Meta:
        model = Shift
        fields = ['worker', 'location', 'date', 'start_time', 'end_time', 'sleep_in', 'is_completed', 'signature', 'signed_by']
        widgets = {
            'worker': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'sleep_in': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_completed': forms.Select(attrs={'class': 'form-control'}),
            'signature': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'signed_by': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['worker'].queryset = User.objects.filter(is_staff=False)
        self.fields['location'].queryset = Location.objects.all()
        self.fields['is_completed'].choices = [(True, 'Yes'), (False, 'No')]

class AvailabilityForm(forms.ModelForm):
    dates = forms.CharField(widget=forms.TextInput(attrs={'class': 'datepicker'}))
    is_available = forms.BooleanField(required=False)

    class Meta:
        model = Availability
        fields = ['dates', 'is_available']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'content']

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2','is_admin', 'is_worker']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
            'is_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_worker': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class WorkerUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = WorkerProfile
        fields = ['signature']
        widgets = {
            'signature': forms.Textarea(attrs={'rows': 5, 'cols': 40, 'class': 'form-control'}),
        }
        



class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'rate', 'address', 'postcode', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control'}),
            'postcode': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
        }