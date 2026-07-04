from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Category, TrainingTrack, InternshipPosting, Application, AttendanceRecord, University, UserProfile, CompanyProfile
from django.contrib.auth.models import User

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
        
    # Get applicant tracking updates
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

def apply_internship_view(request, posting_id):
    posting = get_object_or_404(InternshipPosting, id=posting_id)
    if request.method == 'POST':
        app = Application.objects.create(
            internship=posting,
            student_name=request.POST.get('student_name'),
            university_name=request.POST.get('university_name'),
            email=request.POST.get('email'),
            cv_file=request.FILES.get('cv_file'),
            cpr_file=request.FILES.get('cpr_file'),
            passport_file=request.FILES.get('passport_file'),
            uni_id_file=request.FILES.get('uni_id_file'),
        )
        posting.views_count += 1
        posting.save()
        messages.success(request, "Application submitted successfully with all required documents!")
        return redirect('guest_home' if not request.user.is_authenticated else 'student_dashboard')
    return render(request, 'apply.html', {'posting': posting})

@login_required
def attendance_log_view(request):
    # Workflow A processing engine
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
        return redirect('attendance_log')
        
    my_shifts = AttendanceRecord.objects.filter(user=request.user).order_by('-date')
    verified_hours = sum(r.hours_worked for r in my_shifts if r.is_verified)
    
    # Secure Calendar Serialization Engine
    import json
    calendar_data = {}
    for shift in my_shifts:
        if shift.date:
            date_str = shift.date.strftime('%Y-%m-%d')
            calendar_data[date_str] = {
                'hours': shift.hours_worked,
                'verified': shift.is_verified
            }
    
    context = {
        'record': record,
        'my_shifts': my_shifts,
        'verified_hours': verified_hours,
        'target_hours': 240.0,
        'calendar_data_json': json.dumps(calendar_data)  # Safely passes logs to the frontend
    }
    return render(request, 'attendance_log.html', context)
    
    context = {
        'record': record,
        'my_shifts': my_shifts,
        'verified_hours': verified_hours,
        'target_hours': 240.0
    }
    return render(request, 'attendance_log.html', context)

@login_required
def admin_manage_view(request):
    # Workflow B processing audit queue
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
    profile = get_object_or_404(CompanyProfile, user=request.user)
    my_postings = profile.postings.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        app_id = request.POST.get('app_id')
        app = get_object_or_404(Application, id=app_id)
        if action == 'shortlist':
            app.status = 'Shortlisted'
        elif action == 'reject':
            app.status = 'Rejected'
        app.save()
        messages.success(request, "Applicant status modified successfully.")
        return redirect('company_dashboard')
        
    return render(request, 'company_dashboard.html', {'postings': my_postings})

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