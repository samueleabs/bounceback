# shifts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *

class WorkerSignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

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
    date = forms.DateField(widget=forms.TextInput(attrs={'class': 'form-control datepicker'}))
    is_available = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    class Meta:
        model = Availability
        fields = ['date', 'is_available']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['receiver', 'content']

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
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

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']



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