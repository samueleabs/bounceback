# shifts/views.py
from django.conf import settings
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, PasswordChangeForm
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Shift, Availability, Message, User
from .forms import *
from django.contrib.auth import views as auth_views
from datetime import datetime, timedelta, date
from django.db.models import Count
from django.http import HttpResponse
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.db.models import Count
from django.utils import timezone
import json
from django.core.serializers.json import DjangoJSONEncoder
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font
import tempfile
from .utils import *


def landing_page(request):
    if request.user.is_authenticated:
        if request.user.is_admin:
            return redirect('admin_dashboard')
        elif request.user.is_worker:
            return redirect('worker_shift_list')
    return render(request, 'landing_page.html')

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_admin:
                    return redirect('admin_dashboard')
                elif user.is_worker:
                    return redirect('worker_shift_list')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('user_login')

class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    def get_success_url(self):
        return reverse_lazy('user_login')

    def get(self, request, *args, **kwargs):
        messages.success(request, 'Your password has been reset successfully. You can now log in with your new password.')
        return super().get(request, *args, **kwargs)
@login_required
def admin_dashboard(request):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    
    total_users = User.objects.count()
    total_shifts = Shift.objects.count()
    total_messages = Message.objects.count()
    recent_shifts = Shift.objects.order_by('-date')[:5]
    unsigned_shifts = Shift.objects.filter(is_completed=False).order_by('-date')[:5]
    
    # Get the selected date from the request
    selected_date_str = request.GET.get('selected_date', '')
    if selected_date_str:
        selected_date = parse_date(selected_date_str)
    else:
        selected_date = datetime.today()
    
    # Calculate the start of the week (Monday)
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    days_of_week = [start_of_week + timedelta(days=i) for i in range(7)]
    shifts_per_day = [
        Shift.objects.filter(date=day).count() for day in days_of_week
    ]
    
    context = {
        'total_users': total_users,
        'total_shifts': total_shifts,
        'total_messages': total_messages,
        'recent_shifts': recent_shifts,
        'unsigned_shifts': unsigned_shifts,
        'days_of_week': json.dumps([day.strftime('%A %Y-%m-%d') for day in days_of_week]),
        'shifts_per_day': json.dumps(shifts_per_day),
        'selected_date': selected_date.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'admin/dashboard.html', context)

    


@login_required
def worker_shift_list(request):
    today = date.today()
    today_shifts = Shift.objects.filter(worker=request.user, date=today)
    upcoming_shifts = Shift.objects.filter(worker=request.user, date__gt=today)
    previous_shifts = Shift.objects.filter(worker=request.user, date__lt=today)
    return render(request, 'worker/worker_shift_list.html', {
        'today_shifts': today_shifts,
        'upcoming_shifts': upcoming_shifts,
        'previous_shifts': previous_shifts
    })

@login_required
def sign_off_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    if request.method == 'POST':
        signature = request.POST.get('signature')
        signed_by = request.POST.get('signed_by')
        if signature and signed_by:
            shift.signature = signature
            shift.is_completed = True
            shift.signed_by = signed_by
            shift.save()
            return redirect('worker_shift_list')
    return render(request, 'worker/sign_off_shift.html', {'shift': shift})

@login_required
def set_availability(request):
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.worker = request.user
            availability.save()
            return redirect('view_profile')
    else:
        form = AvailabilityForm()
    return render(request, 'profile/set_availability.html', {'form': form})

@login_required
def view_availability(request):
    availability = Availability.objects.filter(worker=request.user)
    return render(request, 'profile/view_availability.html', {'availability': availability})

@login_required
def admin_view_availability(request):
    date = request.GET.get('date')
    if date:
        availability = Availability.objects.filter(date=date)
    else:
        availability = Availability.objects.all()
    return render(request, 'admin/admin_view_availability.html', {'availability': availability})

@login_required
def get_availability(request):
    availability = Availability.objects.filter(worker=request.user)
    data = serialize('json', availability)
    return JsonResponse(data, safe=False)

@login_required
def get_admin_availability(request):
    try:
        date = request.GET.get('date')
        if date:
            availability = Availability.objects.filter(date=date)
        else:
            availability = Availability.objects.all()
        data = serialize('json', availability)
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.error(f"Error fetching availability: {e}")
        return JsonResponse({'error': str(e)}, status=500)




def manage_locations(request):
    locations = Location.objects.all()
    return render(request, 'admin/manage_locations.html', {'locations': locations})

def create_location(request):
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_locations')
    else:
        form = LocationForm()
    return render(request, 'admin/create_location.html', {'form': form})

def edit_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return redirect('manage_locations')
    else:
        form = LocationForm(instance=location)
    return render(request, 'admin/edit_location.html', {'form': form, 'location': location})

def delete_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    if request.method == 'POST':
        location.delete()
        return redirect('manage_locations')
    return render(request, 'admin/delete_location.html', {'location': location})


@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('worker_shift_list')
    else:
        form = MessageForm()
    return render(request, 'worker/send_message.html', {'form': form})

@login_required
def manage_shifts(request):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', 'date')
    order = request.GET.get('order', 'asc')
    
    shifts_list = Shift.objects.all()
    
    if search_query:
        shifts_list = shifts_list.filter(
            Q(date__icontains=search_query) |
            Q(start_time__icontains=search_query) |
            Q(end_time__icontains=search_query) |
            Q(location__name__icontains=search_query) |
            Q(is_completed__icontains=search_query)
        )
    
    if order == 'desc':
        sort_by = f'-{sort_by}'
    
    shifts_list = shifts_list.order_by(sort_by)
    
    paginator = Paginator(shifts_list, 10)  # Show 10 shifts per page
    page = request.GET.get('page')
    shifts = paginator.get_page(page)
    
    context = {
        'shifts': shifts,
        'search_query': search_query,
        'sort_by': sort_by,
        'order': order,
    }
    
    return render(request, 'admin/manage_shifts.html', context)

@login_required
def create_shift(request):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_shifts')
    else:
        form = ShiftForm()
    return render(request, 'admin/create_shift.html', {'form': form})

@login_required
def edit_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            return redirect('view_shift', shift_id=shift.id)
    else:
        form = ShiftForm(instance=shift)
    
    return render(request, 'admin/edit_shift.html', {'form': form, 'shift': shift})

@login_required
def delete_shift(request, shift_id):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    shift = get_object_or_404(Shift, id=shift_id)
    if request.method == 'POST':
        shift.delete()
        return redirect('manage_shifts')
    return render(request, 'admin/delete_shift.html', {'shift': shift})

@login_required
def view_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    if request.user.is_admin:
        return render(request, 'admin/view_shift.html', {'shift': shift})
    elif request.user.is_worker and shift.worker == request.user:
        return render(request, 'worker/view_shift.html', {'shift': shift})
    else:
        return redirect('worker_shift_list')

@login_required
def manage_users(request):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    
    users_list = User.objects.all()
    paginator = Paginator(users_list, 10)  # Show 10 users per page
    page = request.GET.get('page')
    users = paginator.get_page(page)
    
    context = {
        'users': users,
    }
    
    return render(request, 'admin/manage_users.html', context)

@login_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('manage_users')
    else:
        form = CustomUserChangeForm(instance=user)
    return render(request, 'admin/edit_user.html', {'form': form, 'user': user})

@login_required
def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # user.set_password('defaultpassword')  # Set default password
            user.save()
            return redirect('manage_users')
    else:
        form = CustomUserCreationForm()
    return render(request, 'admin/create_user.html', {'form': form})

@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('manage_users')
    return render(request, 'admin/delete_user.html', {'user': user})

@login_required
def view_timesheet(request, user_id):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    
    user = get_object_or_404(User, id=user_id)
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday
    
    shifts = Shift.objects.filter(worker=user, date__range=[start_of_week, end_of_week])
    
    return render(request, 'admin/view_timesheet.html', {'user': user, 'shifts': shifts, 'start_of_week': start_of_week, 'end_of_week': end_of_week})


@login_required
def manage_messages(request):
    return render(request, 'admin/manage_messages.html')

class WorkerLogoutView(auth_views.LogoutView):
    next_page = 'landing_page'


@login_required
def view_profile(request):
    profile, created = WorkerProfile.objects.get_or_create(user=request.user)
    return render(request, 'profile/view_profile.html', {'profile': profile})

@login_required
def edit_profile(request):
    if request.user.is_staff:
        user_form = CustomUserChangeForm(instance=request.user)
    else:
        user_form = WorkerUserChangeForm(instance=request.user)
    
    profile, created = WorkerProfile.objects.get_or_create(user=request.user)
    profile_form = UserProfileForm(instance=profile)

    if request.method == 'POST':
        if request.user.is_staff:
            user_form = CustomUserChangeForm(request.POST, instance=request.user)
        else:
            user_form = WorkerUserChangeForm(request.POST, instance=request.user)
        
        profile_form = UserProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            if request.POST.get('clear_signature') == 'true':
                profile.signature = ''
            else:
                signature = request.POST.get('signature')
                if signature:
                    profile.signature = signature
            profile.save()
            return redirect('view_profile')

    return render(request, 'profile/edit_profile.html', {'user_form': user_form, 'profile_form': profile_form, 'profile': profile})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            return redirect('view_profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'profile/change_password.html', {'form': form})

def admin_reset_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password was successfully updated for user: {}'.format(user.username))
            return redirect('manage_users')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = SetPasswordForm(user)
    return render(request, 'admin/admin_reset_password.html', {'form': form, 'user': user})

def manage_timesheets(request):
    today = timezone.now().date()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    
    # Filter for shifts that are completed and signed
    shifts = Shift.objects.filter(date__range=[last_monday, last_sunday], is_completed=True, signature__isnull=False)
    users_with_due_timesheets = User.objects.filter(shift__in=shifts).distinct()
    
    # Add a flag to indicate whether the timesheet is generated
    users_with_timesheet_status = []
    for user in users_with_due_timesheets:
        timesheet_generated = shifts.filter(worker=user, timesheet_generated=True).exists()
        users_with_timesheet_status.append({
            'user': user,
            'timesheet_generated': timesheet_generated
        })
    
    return render(request, 'admin/manage_timesheets.html', {'users_with_timesheet_status': users_with_timesheet_status})

def generate_timesheet(request, user_id):
    user = get_object_or_404(User, id=user_id)
    today = timezone.now().date()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    
    # Logic to generate timesheet for the user for the previous week
    # For now, we will just mark the timesheet as generated
    # You can add your actual timesheet generation logic here
    shifts = Shift.objects.filter(worker=user, date__range=[last_monday, last_sunday], is_completed=True, signature__isnull=False)
    for shift in shifts:
        shift.timesheet_generated = True  # Assuming you have a field to mark timesheet generation
        shift.save()
    
    return redirect('view_timesheet', user_id=user.id)
    
@login_required
def view_timesheet(request, user_id):
    user = get_object_or_404(User, id=user_id)
    today = timezone.now().date()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    
    shifts = Shift.objects.filter(worker=user, date__range=[last_monday, last_sunday], is_completed=True, signature__isnull=False)
    
    # Group shifts by location
    shifts_by_location = defaultdict(list)
    for shift in shifts:
        shifts_by_location[shift.location.name].append({
            'date': shift.date.strftime('%Y-%m-%d'),
            'start_time': shift.start_time.strftime('%H:%M'),
            'end_time': shift.end_time.strftime('%H:%M'),
            'is_completed': shift.is_completed,
            'signed_by': shift.signed_by
        })
    
    shifts_by_location_json = json.dumps(shifts_by_location, cls=DjangoJSONEncoder)
    
    return render(request, 'admin/view_timesheet.html', {'user': user, 'locations': shifts_by_location.keys(), 'shifts_by_location_json': shifts_by_location_json})

import logging
logger = logging.getLogger(__name__)




@login_required
def download_timesheet_pdf(request, user_id):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    
    user = get_object_or_404(User, id=user_id)
    location_name = request.GET.get('location')
    
    if not location_name:
        return HttpResponse("Location not specified", status=400)
    
    today = timezone.now().date()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    
    shifts = Shift.objects.filter(worker=user, location__name=location_name, date__range=[last_monday, last_sunday], is_completed=True, signature__isnull=False)
    
    if not shifts.exists():
        return HttpResponse("No shifts found for the specified location and date range", status=404)
    
    return generate_timesheet_pdf(user, location_name, shifts, last_monday, last_sunday)


@login_required
def download_timesheet_excel(request, user_id):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    
    user = get_object_or_404(User, id=user_id)
    location_name = request.GET.get('location')
    
    if not location_name:
        return HttpResponse("Location not specified", status=400)
    
    today = timezone.now().date()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    
    shifts = Shift.objects.filter(worker=user, location__name=location_name, date__range=[last_monday, last_sunday], is_completed=True, signature__isnull=False)
    
    if not shifts.exists():
        return HttpResponse("No shifts found for the specified location and date range", status=404)
    
    return generate_timesheet_excel(user, location_name, shifts, last_monday, last_sunday)