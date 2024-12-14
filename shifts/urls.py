# shifts/urls.py
from django.urls import path
# from .views import landing_page, create_user, delete_user, user_login, worker_shift_list, set_availability, sign_off_shift, send_message, admin_dashboard, manage_shifts, manage_users, view_timesheets, manage_messages, WorkerLogoutView
from .views import *
urlpatterns = [
    path('', landing_page, name='landing_page'),
    path('login/', user_login, name='user_login'),
    path('worker/shifts/', worker_shift_list, name='worker_shift_list'),
    path('worker/set_availability/', set_availability, name='set_availability'),
    path('worker/sign_off_shift/<int:shift_id>/', sign_off_shift, name='sign_off_shift'),
    path('worker/view_shift/<int:shift_id>/', view_shift, name='view_shift'),
    path('worker/send_message/', send_message, name='send_message'),
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('dashboard/manage_shifts/', manage_shifts, name='manage_shifts'),
    path('dashboard/create_shift/', create_shift, name='create_shift'),
    path('dashboard/edit_shift/<int:shift_id>/', edit_shift, name='edit_shift'),
    path('dashboard/delete_shift/<int:shift_id>/', delete_shift, name='delete_shift'),
    path('dashboard/view_shift/<int:shift_id>/', view_shift, name='view_shift'),
    path('dashboard/manage_users/', manage_users, name='manage_users'),
    path('dashboard/create_user/', create_user, name='create_user'),
    path('dashboard/delete_user/<int:user_id>/', delete_user, name='delete_user'),
    path('dashboard/view_timesheets/', view_timesheets, name='view_timesheets'),
    path('dashboard/manage_messages/', manage_messages, name='manage_messages'),
    path('logout/', WorkerLogoutView.as_view(), name='worker_logout'),
]