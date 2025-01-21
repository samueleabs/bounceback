# shifts/views.py
from django.conf import settings
import os
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, PasswordChangeForm
from django.contrib import messages
from django.urls import reverse_lazy
from .models import *
from .forms import *
from django.contrib.auth import views as auth_views
from datetime import datetime, timedelta, date
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
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
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font
import tempfile
from .utils import *
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from decimal import Decimal
from .decorators import admin_required
from pywebpush import webpush, WebPushException
from .notifications import send_push_notification
from firebase_admin import messaging


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
                    return redirect('landing_page')  # Redirect to a default page if user type is not recognized
            else:
                messages.error(request, 'Invalid username or password')
        else:
            messages.error(request, 'Invalid username or password')
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
@admin_required
def admin_dashboard(request):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    
    total_users = User.objects.count()
    total_shifts = Shift.objects.count()
    recent_shifts = Shift.objects.order_by('-date')[:5]
    unsigned_shifts = Shift.objects.filter(is_completed=False, date__lte=date.today()).order_by('-date')[:5]

    
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
        'recent_shifts': recent_shifts,
        'unsigned_shifts': unsigned_shifts,
        'days_of_week': json.dumps([day.strftime('%A %Y-%m-%d') for day in days_of_week]),
        'shifts_per_day': json.dumps(shifts_per_day),
        'selected_date': selected_date.strftime('%Y-%m-%d'),
        'firebase_config': settings.FIREBASE_CONFIG,
    }
    
    return render(request, 'admin/dashboard.html', context)

    


@login_required
@never_cache
def worker_shift_list(request):
    today = timezone.now().date()
    now = timezone.now().time()

    # Filter unsigned shifts that are past their end time
    unsigned_shifts = Shift.objects.filter(
        worker=request.user,
        date__lt=today,
        is_completed=False
    ).distinct()

    # Filter shifts that start today or end today, and are not completed, excluding unsigned shifts
    today_shifts = Shift.objects.filter(
        worker=request.user
    ).filter(
        (Q(date=today) | Q(date=today - timedelta(days=1), end_time__gt=now)) & Q(is_completed=False)
    ).exclude(id__in=unsigned_shifts.values('id')).distinct()

    upcoming_shifts = Shift.objects.filter(worker=request.user, date__gt=today)
    previous_shifts = Shift.objects.filter(worker=request.user, date__lt=today, is_completed=True)

    unread_notifications_count = Notification.objects.filter(user=request.user, read=False).count()
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:3]

    context = {
        'today_shifts': today_shifts,
        'unsigned_shifts': unsigned_shifts,
        'upcoming_shifts': upcoming_shifts,
        'previous_shifts': previous_shifts,
        'unread_notifications_count': unread_notifications_count,
        'notifications': recent_notifications,
        'firebase_config': settings.FIREBASE_CONFIG,
    }

    return render(request, 'worker/worker_shift_list.html', context)


@login_required
def worker_view_timesheet(request):
    user = request.user
    today = timezone.now().date()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)

    shifts = Shift.objects.filter(worker=user, date__range=[last_monday, last_sunday], is_completed=True, signature__isnull=False)

    unread_notifications_count = Notification.objects.filter(user=request.user, read=False).count()
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:3]

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

    context = {
        'user': user,
        'locations': shifts_by_location.keys(),
        'shifts_by_location_json': shifts_by_location_json,
        'unread_notifications_count': unread_notifications_count,
        'notifications': recent_notifications,
    }

    return render(request, 'worker/view_timesheet.html', context)



@login_required
def sign_off_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    unread_notifications_count = Notification.objects.filter(user=request.user, read=False).count()
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:3]
    if request.method == 'POST':
        signature = request.POST.get('signature')
        signed_by = request.POST.get('signed_by')
        if signature and signed_by:
            shift.signature = signature
            shift.is_completed = True
            shift.signed_by = signed_by
            shift.save()
            # Force database refresh
            shift.refresh_from_db()
            return redirect('worker_shift_list')
    return render(request, 'worker/sign_off_shift.html', {'shift': shift, 
        'unread_notifications_count': unread_notifications_count,
        'notifications': recent_notifications})

@login_required
def set_availability(request):
    unread_notifications_count = Notification.objects.filter(user=request.user, read=False).count()
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:3]
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            dates = form.cleaned_data['dates'].split(',')
            is_available = form.cleaned_data['is_available']
            for date in dates:
                Availability.objects.create(worker=request.user, date=date.strip(), is_available=is_available)
            return redirect('view_availability')
    else:
        form = AvailabilityForm()
    return render(request, 'worker/set_availability.html', {'form': form,'notifications': recent_notifications,'unread_notifications_count': unread_notifications_count,})

@login_required
def view_availability(request):
    availability = Availability.objects.filter(worker=request.user).order_by('date')
    unread_notifications_count = Notification.objects.filter(user=request.user, read=False).count()
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:3]
    return render(request, 'worker/view_availability.html', {'availability': availability,'notifications': recent_notifications,'unread_notifications_count': unread_notifications_count,})

@login_required
@admin_required
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
def delete_availability(request, availability_id):
    availability = get_object_or_404(Availability, id=availability_id)
    if request.method == 'POST':
        availability.delete()
        return redirect('view_availability')
    return render(request, 'worker/delete_availability.html', {'availability': availability})

@login_required
@admin_required
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



@login_required
@admin_required
def manage_locations(request):
    locations = Location.objects.all()
    return render(request, 'admin/manage_locations.html', {'locations': locations})

@login_required
@admin_required
def create_location(request):
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_locations')
    else:
        form = LocationForm()
    return render(request, 'admin/create_location.html', {'form': form})

@login_required
@admin_required
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

@login_required
@admin_required
def delete_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    if request.method == 'POST':
        location.delete()
        return redirect('manage_locations')
    return render(request, 'admin/delete_location.html', {'location': location})




@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'worker/notifications.html', {'notifications': notifications})

@login_required
def clear_notifications(request):
    Notification.objects.filter(user=request.user).delete()
    return redirect('notifications')

@login_required
def mark_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    notification.read = True
    notification.save()
    return redirect('notifications')


@login_required
@admin_required
def manage_shifts(request):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', 'date')
    order = request.GET.get('order', 'asc')
    
    shifts_list = Shift.objects.select_related('worker', 'location').all()
    
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
    
    context = {
        'shifts': shifts_list,
        'search_query': search_query,
        'sort_by': sort_by,
        'order': order,
    }
    
    return render(request, 'admin/manage_shifts.html', context)

@login_required
@admin_required
def create_shift(request):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    
    existing_shifts = None
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            worker = form.cleaned_data['worker']
            date = form.cleaned_data['date']
            existing_shifts = Shift.objects.filter(worker=worker, date=date)
            if existing_shifts.exists():
                # Show warning modal with existing shift details
                return render(request, 'admin/create_shift.html', {
                    'form': form,
                    'existing_shifts': existing_shifts,
                    'show_warning': True
                })
            else:
                shift = form.save()
                Notification.objects.create(user=shift.worker, content=f"New shift assigned on {shift.date}")
                if shift.worker.webpush_subscription:
                    send_push_notification(shift.worker.webpush_subscription, f"New shift assigned on {shift.date}")
                return redirect('manage_shifts')
    else:
        form = ShiftForm()
    
    return render(request, 'admin/create_shift.html', {'form': form, 'existing_shifts': existing_shifts, 'show_warning': False, 'firebase_config': settings.FIREBASE_CONFIG,})

@login_required
@admin_required
def edit_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    
    existing_shifts = None
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            worker = form.cleaned_data['worker']
            date = form.cleaned_data['date']
            existing_shifts = Shift.objects.filter(worker=worker, date=date).exclude(id=shift_id)
            if existing_shifts.exists():
                # Show warning modal with existing shift details
                return render(request, 'admin/edit_shift.html', {
                    'form': form,
                    'shift': shift,
                    'existing_shifts': existing_shifts,
                    'show_warning': True
                })
            else:
                form.save()
                Notification.objects.create(user=shift.worker, content=f"Shift on {shift.date} changes made.")
                return redirect('view_shift', shift_id=shift.id)
    else:
        form = ShiftForm(instance=shift)
    
    return render(request, 'admin/edit_shift.html', {'form': form, 'shift': shift, 'existing_shifts': existing_shifts, 'show_warning': False, 'firebase_config': settings.FIREBASE_CONFIG,})

@login_required
@admin_required
def delete_shift(request, shift_id):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    shift = get_object_or_404(Shift, id=shift_id)
    if request.method == 'POST':
        Notification.objects.create(user=shift.worker, content=f"Shift on {shift.date} has been dropped.")
        if shift.worker.webpush_subscription:
                    send_push_notification(shift.worker.webpush_subscription, f"Shift on {shift.date} has been dropped.")
        shift.delete()
        return redirect('manage_shifts')
    return render(request, 'admin/delete_shift.html', {'shift': shift, 'firebase_config': settings.FIREBASE_CONFIG,})

@login_required
def view_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    unread_notifications_count = Notification.objects.filter(user=request.user, read=False).count()
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:3]
    if request.user.is_admin:
        return render(request, 'admin/view_shift.html', {'shift': shift})
    elif request.user.is_worker and shift.worker == request.user:
        return render(request, 'worker/view_shift.html', {'shift': shift,'notifications': recent_notifications,'unread_notifications_count': unread_notifications_count,})
    else:
        return redirect('worker_shift_list',)

@login_required
@admin_required
def manage_users(request):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    
    users = User.objects.all()  # Get all users without pagination
    
    context = {
        'users': users,
    }
    
    return render(request, 'admin/manage_users.html', context)

@login_required
@admin_required
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
@admin_required
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
@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('manage_users')
    return render(request, 'admin/delete_user.html', {'user': user})

@login_required
@admin_required
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
def worker_view_profile(request):
    profile, created = WorkerProfile.objects.get_or_create(user=request.user)
    unread_notifications_count = Notification.objects.filter(user=request.user, read=False).count()
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:3]
    return render(request, 'worker/worker_view_profile.html', {'profile': profile,'notifications': recent_notifications,'unread_notifications_count': unread_notifications_count,})

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
def worker_edit_profile(request):
    if request.user.is_staff:
        user_form = CustomUserChangeForm(instance=request.user)
    else:
        user_form = WorkerUserChangeForm(instance=request.user)
    
    profile, created = WorkerProfile.objects.get_or_create(user=request.user)
    profile_form = UserProfileForm(instance=profile)
    unread_notifications_count = Notification.objects.filter(user=request.user, read=False).count()
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:3]

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
            return redirect('worker_view_profile')

    return render(request, 'worker/worker_edit_profile.html', {'user_form': user_form, 'profile_form': profile_form, 'profile': profile,
        'unread_notifications_count': unread_notifications_count,
        'notifications': recent_notifications})


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


@login_required
def worker_change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            return redirect('worker_view_profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'worker/worker_change_password.html', {'form': form})

@login_required
@admin_required
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

@login_required
@admin_required
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
            'timesheet_generated': timesheet_generated,
            'firebase_config': settings.FIREBASE_CONFIG,
        })
    
    return render(request, 'admin/manage_timesheets.html', {'users_with_timesheet_status': users_with_timesheet_status})

@login_required
@admin_required
def generate_timesheet(request, user_id, date):
    user = get_object_or_404(User, id=user_id)
    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        # Handle invalid date format
        return redirect('some_error_page')

    last_monday = selected_date
    last_sunday = last_monday + timedelta(days=6)
    
    # Logic to generate timesheet for the user for the selected week
    shifts = Shift.objects.filter(worker=user, date__range=[last_monday, last_sunday], is_completed=True, signature__isnull=False)
    for shift in shifts:
        shift.timesheet_generated = True  # Assuming you have a field to mark timesheet generation
        shift.save()

    # Create a notification for the worker
    Notification.objects.create(user=user, content=f"Timesheet generated for the week of {last_monday.strftime('%Y-%m-%d')} to {last_sunday.strftime('%Y-%m-%d')}")
    
    return redirect('view_timesheet', user_id=user.id, date=date,)

@login_required
@admin_required
def view_timesheet(request, user_id, date):
    user = get_object_or_404(User, id=user_id)
    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        # Handle invalid date format
        return redirect('some_error_page')

    last_monday = selected_date
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
    
    return render(request, 'admin/view_timesheet.html', {'user': user, 'locations': shifts_by_location.keys(), 'shifts_by_location_json': shifts_by_location_json, 'date': date})

import logging
logger = logging.getLogger(__name__)




@login_required
def download_timesheet_pdf(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Ensure that workers can only download their own timesheets
    if not request.user.is_admin and request.user != user:
        return redirect('worker_shift_list')
    
    location_name = request.GET.get('location')
    date_str = request.GET.get('date')
    
    # logger.debug(f"Location: {location_name}, Date: {date_str}")
    
    if not location_name:
        return HttpResponse("Location not specified", status=400)
    
    if not date_str:
        # logger.error("Date parameter is missing")
        return HttpResponse("Date parameter is missing", status=400)
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        # logger.error(f"Invalid date format: {date_str}")
        return HttpResponse("Invalid date format", status=400)
    
    last_monday = selected_date - timedelta(days=selected_date.weekday())
    last_sunday = last_monday + timedelta(days=6)
    
    shifts = Shift.objects.filter(worker=user, location__name=location_name, date__range=[last_monday, last_sunday], is_completed=True, signature__isnull=False)
    
    if not shifts.exists():
        # logger.error(f"No shifts found for the selected location and date range: {location_name}, {last_monday} to {last_sunday}")
        return HttpResponse("No shifts found for the selected location and date range", status=404)
    
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


@login_required
@admin_required
def admin_reporting(request):
    if not request.user.is_admin:
        return redirect('worker_shift_list')

    users = User.objects.all()
    selected_users = []
    shifts = []
    total_hours = Decimal(0)
    total_pay = Decimal(0)

    if request.method == 'POST':
        user_ids = request.POST.getlist('users')
        start_date_str = request.POST.get('start_date')

        selected_users = User.objects.filter(id__in=user_ids)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = start_date + timedelta(days=6)

        for user in selected_users:
            user_shifts = Shift.objects.filter(worker=user, date__range=[start_date, end_date], is_completed=True)
            for shift in user_shifts:
                # Calculate hours done
                start_time = datetime.combine(date.min, shift.start_time)
                end_time = datetime.combine(date.min, shift.end_time)
                hours_done = Decimal((end_time - start_time).seconds) / Decimal(3600)
                total_hours += hours_done

                location = shift.location
                # Calculate shift pay based on the day of the week
                if shift.date.weekday() == 5:  # Saturday
                    shift_pay = hours_done * location.saturday_rate
                elif shift.date.weekday() == 6:  # Sunday
                    shift_pay = hours_done * location.sunday_rate
                else:  # Weekday
                    shift_pay = hours_done * location.weekday_rate

                # Add sleep-in rate if applicable
                if shift.sleep_in:
                    shift_pay += location.sleep_in_rate

                total_pay += shift_pay
                shift.shift_pay = shift_pay  # Add shift_pay attribute to shift for display in the template
                shift.hours_done = hours_done  # Add hours_done attribute to shift for display in the template
                shift.rate = location.weekday_rate if shift.date.weekday() < 5 else (location.saturday_rate if shift.date.weekday() == 5 else location.sunday_rate)
                shifts.append(shift)

    context = {
        'users': users,
        'selected_users': [user.id for user in selected_users],
        'shifts': shifts,
        'total_hours': total_hours,
        'total_pay': total_pay,
        'start_date': start_date_str if request.method == 'POST' else '',
    }

    return render(request, 'admin/admin_reporting.html', context)


@login_required
def export_report_to_excel(request):
    if not request.user.is_admin:
        return redirect('worker_shift_list')

    user_ids_str = request.GET.get('users')
    start_date_str = request.GET.get('start_date')

    user_ids = [int(id) for id in user_ids_str.split(',')]
    selected_users = User.objects.filter(id__in=user_ids)
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = start_date + timedelta(days=6)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Shifts Report"

    # Write header
    headers = ["User", "Date", "Start Time", "End Time", "Location", "Hours Done", "Rate", "Sleep In", "Amount Paid"]
    ws.append(headers)

    for user in selected_users:
        user_shifts = Shift.objects.filter(worker=user, date__range=[start_date, end_date], is_completed=True)
        for shift in user_shifts:
            # Calculate hours done
            start_time = datetime.combine(date.min, shift.start_time)
            end_time = datetime.combine(date.min, shift.end_time)
            hours_done = Decimal((end_time - start_time).seconds) / Decimal(3600)

            location = shift.location
            # Calculate shift pay based on the day of the week
            if shift.date.weekday() == 5:  # Saturday
                shift_pay = hours_done * location.saturday_rate
            elif shift.date.weekday() == 6:  # Sunday
                shift_pay = hours_done * location.sunday_rate
            else:  # Weekday
                shift_pay = hours_done * location.weekday_rate

            # Add sleep-in rate if applicable
            if shift.sleep_in:
                shift_pay += location.sleep_in_rate

            rate = location.weekday_rate if shift.date.weekday() < 5 else (location.saturday_rate if shift.date.weekday() == 5 else location.sunday_rate)
            row = [
                f"{user.first_name} {user.last_name}",
                shift.date.strftime("%Y-%m-%d"),
                shift.start_time.strftime("%H:%M"),
                shift.end_time.strftime("%H:%M"),
                shift.location.name,
                float(hours_done),
                float(rate),
                "Yes" if shift.sleep_in else "No",
                float(shift_pay)
            ]
            ws.append(row)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=shifts_report.xlsx'
    wb.save(response)
    return response

@login_required
def firebase_config_view(request):
    print("Firebase Config:", settings.FIREBASE_CONFIG)
    context = {
        'firebase_config': settings.FIREBASE_CONFIG,
    }
    return render(request, 'base_generic.html', context)

@login_required
def update_subscription(request):
    if request.method == 'POST':
        subscription_info = json.loads(request.body)
        request.user.webpush_subscription = subscription_info
        request.user.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)
    
def service_worker_view(request):
    firebase_config = settings.FIREBASE_CONFIG
    sw_content = render_to_string('firebase-messaging-sw.js', {'firebase_config': firebase_config})
    return HttpResponse(sw_content, content_type='application/javascript')