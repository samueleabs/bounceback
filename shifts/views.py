# shifts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm 
# from django.contrib.auth.models import User
from .models import Shift, Availability, Message, User
# from .forms import ShiftForm, AvailabilityForm, MessageForm, AuthenticationForm, CustomUserCreationForm
from .forms import *
from django.contrib.auth import views as auth_views

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

@login_required
def admin_dashboard(request):
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    return render(request, 'admin/dashboard.html')

@login_required
def worker_shift_list(request):
    shifts = Shift.objects.filter(worker=request.user)
    return render(request, 'worker/shift_list.html', {'shifts': shifts})

@login_required
def set_availability(request):
    if request.method == 'POST':
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('worker_shift_list')
    else:
        form = AvailabilityForm()
    return render(request, 'worker/set_availability.html', {'form': form})

@login_required
def sign_off_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    if request.method == 'POST':
        signature = request.POST.get('signature')
        if signature:
            shift.signature = signature
            shift.is_completed = True
            shift.save()
            return redirect('worker_shift_list')
    return render(request, 'worker/sign_off_shift.html', {'shift': shift})

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
    shifts = Shift.objects.all()
    return render(request, 'admin/manage_shifts.html', {'shifts': shifts})

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
    if not request.user.is_admin:
        return redirect('worker_shift_list')
    shift = get_object_or_404(Shift, id=shift_id)
    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            form.save()
            return redirect('manage_shifts')
    else:
        form = ShiftForm(instance=shift)
    return render(request, 'admin/edit_shift.html', {'form': form})

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
    users = User.objects.filter(is_superuser=False)  # Fetch non-superuser users
    return render(request, 'admin/manage_users.html', {'users': users})

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
def view_timesheets(request):
    return render(request, 'admin/view_timesheets.html')

@login_required
def manage_messages(request):
    return render(request, 'admin/manage_messages.html')

class WorkerLogoutView(auth_views.LogoutView):
    next_page = 'landing_page'