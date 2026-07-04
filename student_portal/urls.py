from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.guest_home_view, name='guest_home'),
    path('dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('apply/<int:posting_id>/', views.apply_internship_view, name='apply_internship'),
    path('attendance/log/', views.attendance_log_view, name='attendance_log'),
    path('admin-manage/', views.admin_manage_view, name='admin_manage'),
    path('company/dashboard/', views.company_dashboard_view, name='company_dashboard'),
    path('seeker/resume/', views.resume_builder_view, name='resume_builder'),
    
    # Global Native Authentication Routes
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='guest_home'), name='logout'),
]