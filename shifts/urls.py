# shifts/urls.py
from django.urls import path
# from .views import landing_page, create_user, delete_user, user_login, worker_shift_list, set_availability, sign_off_shift, send_message, admin_dashboard, manage_shifts, manage_users, view_timesheets, manage_messages, WorkerLogoutView
from .views import *
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('login/', user_login, name='user_login'),
    path('worker/shifts/', worker_shift_list, name='worker_shift_list'),
    path('worker/set_availability/', set_availability, name='set_availability'),
    path('worker/view_availability/', view_availability, name='view_availability'),
    path('worker/get_availability/', get_availability, name='get_availability'),
    path('worker/delete_availability/<int:availability_id>/', delete_availability, name='delete_availability'),
    path('dashboard/admin_view_availability/', admin_view_availability, name='admin_view_availability'),
    path('dashboard/get_admin_availability/', get_admin_availability, name='get_admin_availability'),
    path('worker/sign_off_shift/<int:shift_id>/', sign_off_shift, name='sign_off_shift'),
    path('worker/view_shift/<int:shift_id>/', view_shift, name='view_shift'),
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('dashboard/manage_shifts/', manage_shifts, name='manage_shifts'),
    path('dashboard/create_shift/', create_shift, name='create_shift'),
    path('dashboard/edit_shift/<int:shift_id>/', edit_shift, name='edit_shift'),
    path('dashboard/delete_shift/<int:shift_id>/', delete_shift, name='delete_shift'),
    path('dashboard/view_shift/<int:shift_id>/', view_shift, name='view_shift'),
    path('dashboard/manage_users/', manage_users, name='manage_users'),
    path('dashboard/create_user/', create_user, name='create_user'),
    path('dashboard/edit_user/<int:user_id>/', edit_user, name='edit_user'),
    path('dashboard/reset_password/<int:user_id>/', admin_reset_password, name='admin_reset_password'),
    path('dashboard/delete_user/<int:user_id>/', delete_user, name='delete_user'),
    path('dashboard/view_timesheet/<int:user_id>/', view_timesheet, name='view_timesheet'),
    path('dashboard/download_timesheet_excel/<int:user_id>/', download_timesheet_excel, name='download_timesheet_excel'),
    path('dashboard/download_timesheet_pdf/<int:user_id>/', download_timesheet_pdf, name='download_timesheet_pdf'),
    path('dashboard/manage_locations/', manage_locations, name='manage_locations'),
    path('dashboard/create_location/', create_location, name='create_location'),
    path('dashboard/edit_location/<int:location_id>/', edit_location, name='edit_location'),
    path('dashboard/delete_location/<int:location_id>/', delete_location, name='delete_location'),
    path('dashboard/manage_messages/', manage_messages, name='manage_messages'),
    path('dashboard/manage_timesheets/', manage_timesheets, name='manage_timesheets'),
    path('dashboard/generate_timesheet/<int:user_id>/', generate_timesheet, name='generate_timesheet'),
    path('profile/', view_profile, name='view_profile'),
    path('worker/profile', worker_view_profile, name='worker_view_profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('worker/edit/', worker_edit_profile, name='worker_edit_profile'),
    path('profile/change_password/', change_password, name='change_password'),
    path('worker/change_password/', worker_change_password, name='worker_change_password'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('notifications/', notifications, name='notifications'),
    path('notifications/clear/', clear_notifications, name='clear_notifications'),
    path('notifications/mark_as_read/<int:notification_id>/', mark_as_read, name='mark_as_read'),
    path('logout/', WorkerLogoutView.as_view(), name='worker_logout'),
]