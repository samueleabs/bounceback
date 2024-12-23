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
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
import tempfile



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
    return render(request, 'profile/view_profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('view_profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'profile/edit_profile.html', {'form': form})

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
def download_timesheet_image(request, user_id):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    
    user = get_object_or_404(User, id=user_id)
    location_name = request.GET.get('location')
    
    if not location_name:
        logger.error("Location not specified")
        return HttpResponse("Location not specified", status=400)
    
    today = timezone.now().date()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    
    shifts = Shift.objects.filter(worker=user, location__name=location_name, date__range=[last_monday, last_sunday], is_completed=True, signature__isnull=False)
    
    if not shifts.exists():
        logger.error("No shifts found for the specified location and date range")
        return HttpResponse("No shifts found for the specified location and date range", status=404)
    
    # Create an image with higher resolution
    width, height = 1600, 1400
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 24)  # Use a truetype font for better quality
    header_font = ImageFont.truetype("arial.ttf", 48)  # Larger font for the header
    
    # Load the logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'bblogo.png')
    try:
        logo = Image.open(logo_path)
    except FileNotFoundError:
        logger.error(f"Logo file not found at {logo_path}")
        return HttpResponse("Logo file not found", status=404)
    
    logo.thumbnail((200, 200))
    image.paste(logo, (20, 60))  # Lower the logo
    
    # Draw the header
    draw.text((240, 60), "Temporary Agency Worker – Time Sheet", font=header_font, fill='darkblue')
    draw.text((240, 140), f"Worker: {user.first_name} {user.last_name}", font=font, fill='black')
    draw.text((240, 180), f"Week: {last_monday.strftime('%Y-%m-%d')} to {last_sunday.strftime('%Y-%m-%d')}", font=font, fill='black')
    
    # Add more spacing between the header and the column headers
    y = 280
    headers = ["Date", "Start Time", "End Time", "Hours Done", "Sleep In", "Signature", "Signed By"]
    x_positions = [20, 220, 420, 620, 820, 1020, 1220]
    for i, header in enumerate(headers):
        draw.text((x_positions[i], y), header, font=font, fill='black')
    
    # Add more spacing between the column headers and the first entry
    y += 60
    total_hours = 0
    total_sleep_in = 0
    row_height = 100  # Increase the row height for better spacing
    for shift in shifts:
        hours_done = (datetime.combine(date.min, shift.end_time) - datetime.combine(date.min, shift.start_time)).seconds / 3600
        total_hours += hours_done
        total_sleep_in += 1 if shift.sleep_in else 0
        
        draw.text((20, y), shift.date.strftime('%Y-%m-%d'), font=font, fill='black')
        draw.text((220, y), shift.start_time.strftime('%H:%M'), font=font, fill='black')
        draw.text((420, y), shift.end_time.strftime('%H:%M'), font=font, fill='black')
        draw.text((620, y), f"{hours_done:.2f}", font=font, fill='black')
        draw.text((820, y), "Yes" if shift.sleep_in else "No", font=font, fill='black')
        
        if shift.signature:
            try:
                # Decode the base64 signature
                signature_data = shift.signature.split(',')[1]
                signature_image = Image.open(BytesIO(base64.b64decode(signature_data)))
                signature_image = signature_image.convert("RGBA")  # Ensure the image has an alpha channel
                
                # Create a white background image
                white_bg = Image.new("RGB", signature_image.size, "white")
                white_bg.paste(signature_image, (0, 0), signature_image)
                signature_image = white_bg
                
                signature_image.thumbnail((200, 80))  # Adjust the thumbnail size to fit within the row
                
                # Paste the signature image onto the main image
                image.paste(signature_image, (1020, y))
            except Exception as e:
                logger.error(f"Error processing signature for shift {shift.id}: {e}")
        
        # Handle case where shift.signed_by might be None
        signed_by = shift.signed_by if shift.signed_by else "N/A"
        draw.text((1220, y), signed_by, font=font, fill='black')
        
        y += row_height  # Adjust the spacing for the next shift
    
    # Add more spacing between the last entry and the totals
    y += 60
    draw.text((20, y), "Total", font=font, fill='black')
    draw.text((620, y), f"{total_hours:.2f}", font=font, fill='black')
    draw.text((820, y), f"{total_sleep_in}", font=font, fill='black')
    
    # Save the image to a BytesIO object
    image_io = BytesIO()
    image.save(image_io, format='PNG')
    image_io.seek(0)
    
    # Create the response
    response = HttpResponse(image_io, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename=timesheet_{user.first_name}_{user.last_name}_{location_name}_{last_monday.strftime("%Y-%m-%d")}_to_{last_sunday.strftime("%Y-%m-%d")}.png'
    
    return response

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
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Time Sheet"
    
    # Add the header
    ws.merge_cells('A1:G1')
    ws['A1'] = "Temporary Agency Worker – Time Sheet"
    ws['A1'].font = Font(size=24, bold=True, color="0000FF")
    
    ws['A2'] = f"Worker: {user.first_name} {user.last_name}"
    ws['A3'] = f"Week: {last_monday.strftime('%Y-%m-%d')} to {last_sunday.strftime('%Y-%m-%d')}"
    
    # Add the table headers
    headers = ["Date", "Start Time", "End Time", "Hours Done", "Sleep In", "Signature", "Signed By"]
    ws.append(headers)
    
    total_hours = 0
    total_sleep_in = 0
    for shift in shifts:
        hours_done = (datetime.combine(date.min, shift.end_time) - datetime.combine(date.min, shift.start_time)).seconds / 3600
        total_hours += hours_done
        total_sleep_in += 1 if shift.sleep_in else 0
        
        row = [
            shift.date.strftime('%Y-%m-%d'),
            shift.start_time.strftime('%H:%M'),
            shift.end_time.strftime('%H:%M'),
            f"{hours_done:.2f}",
            "Yes" if shift.sleep_in else "No",
            "Signature",  # Placeholder for signature
            shift.signed_by if shift.signed_by else "N/A"
        ]
        ws.append(row)
    
    # Add the totals row
    ws.append(["Total", "", "", f"{total_hours:.2f}", f"{total_sleep_in}", "", ""])
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=timesheet_{user.first_name}_{user.last_name}_{location_name}_{last_monday.strftime("%Y-%m-%d")}_to_{last_sunday.strftime("%Y-%m-%d")}.xlsx'
    wb.save(response)
    
    return response

@login_required
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
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=timesheet_{user.first_name}_{user.last_name}_{location_name}_{last_monday.strftime("%Y-%m-%d")}_to_{last_sunday.strftime("%Y-%m-%d")}.pdf'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # Offset everything lower on the page
    y_offset = 100
    
    # Draw the logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'bblogo.png')
    try:
        logo = Image.open(logo_path)
        logo_width, logo_height = logo.size
        aspect_ratio = logo_width / logo_height
        logo_width = (width - 40) * 0.8  # Scale down the logo width by 20%
        logo_height = logo_width / aspect_ratio
        p.drawImage(logo_path, 20, height - logo_height - 20, width=logo_width, height=logo_height)
    except FileNotFoundError:
        logger.error(f"Logo file not found at {logo_path}")
        return HttpResponse("Logo file not found", status=404)
    
    # Draw the header
    p.setFont("Helvetica-Bold", 24)
    p.setFillColorRGB(0, 0, 0.5)  # Dark blue color
    p.drawString(50, height - logo_height - 50 - y_offset, "Temporary Agency Worker – Time Sheet")
    p.setFont("Helvetica", 12)
    p.setFillColorRGB(0, 0, 0)  # Black color
    p.drawString(50, height - logo_height - 80 - y_offset, f"Worker: {user.first_name} {user.last_name}")
    p.drawString(50, height - logo_height - 100 - y_offset, f"Week: {last_monday.strftime('%Y-%m-%d')} to {last_sunday.strftime('%Y-%m-%d')}")
    
    # Add more spacing between the header and the column headers
    y = height - logo_height - 150 - y_offset
    headers = ["Date", "Start Time", "End Time", "Hours Done", "Sleep In", "Signature", "Signed By"]
    x_positions = [50, 120, 190, 260, 330, 400, 470]
    for i, header in enumerate(headers):
        p.drawString(x_positions[i], y, header)
    
    # Add more spacing between the column headers and the first entry
    y -= 40
    total_hours = 0
    total_sleep_in = 0
    row_height = 40  # Increase the row height for better spacing
    for shift in shifts:
        hours_done = (datetime.combine(date.min, shift.end_time) - datetime.combine(date.min, shift.start_time)).seconds / 3600
        total_hours += hours_done
        total_sleep_in += 1 if shift.sleep_in else 0
        
        p.drawString(50, y, shift.date.strftime('%Y-%m-%d'))
        p.drawString(120, y, shift.start_time.strftime('%H:%M'))
        p.drawString(190, y, shift.end_time.strftime('%H:%M'))
        p.drawString(260, y, f"{hours_done:.2f}")
        p.drawString(330, y, "Yes" if shift.sleep_in else "No")
        
        if shift.signature:
            try:
                # Decode the base64 signature
                signature_data = shift.signature.split(',')[1]
                signature_image = Image.open(BytesIO(base64.b64decode(signature_data)))
                signature_image = signature_image.convert("RGBA")  # Ensure the image has an alpha channel
                
                # Create a white background image
                white_bg = Image.new("RGB", signature_image.size, "white")
                white_bg.paste(signature_image, (0, 0), signature_image)
                
                # Increase the resolution of the signature image
                signature_image.thumbnail((50, 20))  # Adjust the thumbnail size to fit within the row
                
                # Create a temporary file for the signature image
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    white_bg.save(tmp_file.name)
                    p.drawImage(tmp_file.name, 400, y - 10, width=50, height=20)
            except Exception as e:
                logger.error(f"Error processing signature for shift {shift.id}: {e}")
        
        signed_by = shift.signed_by if shift.signed_by else "N/A"
        p.drawString(470, y, signed_by)
        
        y -= row_height  # Adjust the spacing for the next shift
    
    # Add more spacing between the last entry and the totals
    y -= 40
    p.drawString(50, y, "Total")
    p.drawString(260, y, f"{total_hours:.2f}")
    p.drawString(330, y, f"{total_sleep_in}")
    
    p.showPage()
    p.save()
    
    return response

