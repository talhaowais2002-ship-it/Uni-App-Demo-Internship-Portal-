from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Category, TrainingTrack, InternshipPosting, Application, AttendanceRecord, University, UserProfile, CompanyProfile, ShiftExcuse
from django.contrib.auth.models import User
import json

def guest_home_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_manage')
        profile = getattr(request.user, 'userprofile', None)
        if profile and profile.role == 'company':
            return redirect('company_dashboard')
        return redirect('student_dashboard')
        
    categories = Category.objects.all()
    return render(request, 'home.html', {'categories': categories, 'is_guest': True})

@login_required
def student_dashboard_view(request):
    categories = Category.objects.all()
    selected_category_id = request.GET.get('category')
    selected_track_id = request.GET.get('track')
    
    tracks = None
    postings = None
    current_category = None
    current_track = None
    
    if selected_category_id:
        current_category = get_object_or_404(Category, id=selected_category_id)
        tracks = current_category.tracks.filter(is_active=True)
        
    if selected_track_id:
        current_track = get_object_or_404(TrainingTrack, id=selected_track_id)
        postings = current_track.postings.filter(is_approved=True)
        
    my_applications = Application.objects.filter(email=request.user.email)
    
    context = {
        'categories': categories,
        'tracks': tracks,
        'postings': postings,
        'current_category': current_category,
        'current_track': current_track,
        'my_applications': my_applications
    }
    return render(request, 'home.html', context)

@login_required
def apply_internship_view(request, posting_id):
    posting = get_object_or_404(InternshipPosting, id=posting_id)
    existing_application = Application.objects.filter(email=request.user.email, internship=posting).exists()
    
    if request.method == 'POST':
        if existing_application:
            messages.warning(request, "You have already submitted an application for this vacancy.")
            return redirect('student_dashboard')
            
        student_name = request.user.get_full_name()
        if not student_name or student_name.strip() == "":
            student_name = request.user.username
            
        university_name = "University of Bahrain"
        try:
            if hasattr(request.user, 'userprofile') and request.user.userprofile:
                prof = request.user.userprofile
                if hasattr(prof, 'university') and prof.university:
                    university_name = str(prof.university)
        except Exception:
            pass
        
        Application.objects.create(
            internship=posting,
            student_name=student_name,
            university_name=university_name,
            email=request.user.email,
            cv_file=request.FILES.get('cv_file'),
            cpr_file=request.FILES.get('cpr_file'),
            passport_file=request.FILES.get('passport_file'),
            uni_id_file=request.FILES.get('uni_id_file'),
            status='Pending Review'
        )
        
        posting.views_count += 1
        posting.save()
        
        messages.success(request, "Your placement application was submitted successfully with all verified documents!")
        return redirect('student_dashboard')

    context = {
        'posting': posting,
        'existing_application': existing_application
    }
    return render(request, 'apply_internship.html', context)

@login_required
def attendance_log_view(request):
    today = timezone.now().date()
    record = AttendanceRecord.objects.filter(user=request.user, date=today).last()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'clock_in':
            if not record or record.check_out is not None:
                AttendanceRecord.objects.create(user=request.user, check_in=timezone.now(), is_verified=False)
                messages.success(request, "Successfully clocked in.")
            else:
                messages.warning(request, "You are already clocked in.")
        elif action == 'clock_out':
            if record and record.check_out is None:
                record.check_out = timezone.now()
                duration = record.check_out - record.check_in
                record.hours_worked = round(duration.total_seconds() / 3600.0, 2)
                record.save()
                messages.success(request, f"Clocked out. Shift duration: {record.hours_worked} hours.")
            else:
                messages.error(request, "No active clock-in event found for today.")
        elif action == 'submit_excuse':
            excuse_date_str = request.POST.get('excuse_date')
            excuse_reason = request.POST.get('excuse_reason')
            if excuse_date_str and excuse_reason:
                from datetime import datetime
                try:
                    excuse_date = datetime.strptime(excuse_date_str, '%Y-%m-%d').date()
                    ShiftExcuse.objects.create(user=request.user, date=excuse_date, reason=excuse_reason)
                    messages.success(request, f"Excuse formally submitted for {excuse_date}.")
                except Exception as e:
                    messages.error(request, "Invalid date format submitted.")
        return redirect('attendance_log')
        
    my_shifts = AttendanceRecord.objects.filter(user=request.user).order_by('-date')
    my_excuses = ShiftExcuse.objects.filter(user=request.user)
    verified_hours = sum(r.hours_worked for r in my_shifts if r.is_verified and r.hours_worked)
    
    calendar_data = {}
    for shift in my_shifts:
        if shift.date:
            date_str = shift.date.strftime('%Y-%m-%d')
            if date_str in calendar_data:
                calendar_data[date_str]['hours'] = round(calendar_data[date_str].get('hours', 0) + (shift.hours_worked or 0), 2)
            else:
                calendar_data[date_str] = {
                    'hours': shift.hours_worked or 0,
                    'status': 'present',
                    'verified': shift.is_verified
                }
                
    for excuse in my_excuses:
        if excuse.date:
            date_str = excuse.date.strftime('%Y-%m-%d')
            if date_str not in calendar_data:
                calendar_data[date_str] = {
                    'hours': 0,
                    'status': 'excused',
                    'verified': excuse.is_approved
                }
    
    context = {
        'record': record,
        'my_shifts': my_shifts,
        'verified_hours': verified_hours,
        'target_hours': 240.0,
        'calendar_data_json': json.dumps(calendar_data)
    }
    return render(request, 'attendance_log.html', context)

@login_required
def admin_manage_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('guest_home')
        
    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        record = get_object_or_404(AttendanceRecord, id=record_id)
        record.is_verified = True
        record.save()
        messages.success(request, f"Shift verified successfully for {record.user.username}.")
        return redirect('admin_manage')
        
    pending_records = AttendanceRecord.objects.filter(is_verified=False, check_out__isnull=False)
    return render(request, 'admin_manage.html', {'pending_records': pending_records})

@login_required
def company_dashboard_view(request):
    """Employer Pipeline: Manage active postings, review applicants, and track hired interns."""
    try:
        profile = request.user.companyprofile
    except Exception:
        messages.error(request, "Access Denied: Your account is not registered as an Internship Provider.")
        return redirect('guest_home')
        
    my_postings = profile.postings.all().order_by('-created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        app_id = request.POST.get('app_id')
        if app_id and action:
            app = get_object_or_404(Application, id=app_id)
            if app.internship.company == profile:
                if action == 'shortlist':
                    app.status = 'Shortlisted'
                elif action == 'reject':
                    app.status = 'Rejected'
                app.save()
                messages.success(request, f"Applicant {app.student_name} marked as {app.status}.")
            return redirect('company_dashboard')
            
    # --- NEW: Fetch Hired Interns & Attendance ---
    hired_apps = Application.objects.filter(internship__company=profile, status='Shortlisted')
    hired_interns_data = []
    
    for app in hired_apps:
        student_user = User.objects.filter(email=app.email).first()
        if student_user:
            attendances = AttendanceRecord.objects.filter(user=student_user).order_by('-date')
            total_verified_hours = sum(r.hours_worked for r in attendances if r.is_verified and r.hours_worked)
            excuses = ShiftExcuse.objects.filter(user=student_user).order_by('-date')
            
            hired_interns_data.append({
                'application': app,
                'student_name': app.student_name,
                'university': app.university_name,
                'total_hours': total_verified_hours,
                'recent_shifts': attendances[:3], # Only show the last 3 shifts on the dashboard
                'recent_excuses': excuses[:2],    # Only show the last 2 excuses on the dashboard
            })
            
    context = {
        'postings': my_postings,
        'hired_interns_data': hired_interns_data
    }
    return render(request, 'company_dashboard.html', context)

@login_required
def post_internship_view(request):
    try:
        profile = request.user.companyprofile
    except Exception:
        messages.error(request, "Access Denied: Employers only.")
        return redirect('guest_home')

    tracks = TrainingTrack.objects.filter(is_active=True)

    if request.method == 'POST':
        InternshipPosting.objects.create(
            company=profile,
            track_id=request.POST.get('track_id'),
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            requirements=request.POST.get('requirements'),
            location=request.POST.get('location'),
            level=request.POST.get('level'),
            nature=request.POST.get('nature'),
            salary_range=request.POST.get('salary_range'),
            education_level=request.POST.get('education_level'),
            is_approved=False
        )
        messages.success(request, "Internship posted successfully! It is currently pending coordinator approval.")
        return redirect('company_dashboard')

    return render(request, 'post_internship.html', {'tracks': tracks})

@login_required
def resume_builder_view(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        profile.cv_summary = request.POST.get('cv_summary')
        profile.cv_skills = request.POST.get('cv_skills')
        profile.cv_experience = request.POST.get('cv_experience')
        profile.cv_education = request.POST.get('cv_education')
        profile.save()
        messages.success(request, "Online Curriculum Vitae updated.")
        return redirect('resume_builder')
    return render(request, 'resume_builder.html', {'profile': profile})