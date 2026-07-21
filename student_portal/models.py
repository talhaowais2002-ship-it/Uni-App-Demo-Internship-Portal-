from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class University(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    branch_code = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "Universities"

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100) # e.g., Computer Science, Business
    icon = models.CharField(max_length=10, default="📁")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class TrainingTrack(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='tracks')
    title = models.CharField(max_length=255) # e.g., Data Entry, Data Analyst
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category.name} - {self.title}"

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Coordinator Admin'),
        ('student', 'Intern Student'),
        ('company', 'Internship Provider'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True)
    training_track = models.ForeignKey(TrainingTrack, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

class ShiftExcuse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    reason = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    # Online CV Builder Data Store Fields
    cv_summary = models.TextField(blank=True, null=True)
    cv_skills = models.TextField(blank=True, null=True, help_text="Comma separated values")
    cv_experience = models.TextField(blank=True, null=True)
    cv_education = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='companyprofile')
    company_name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.company_name

class InternshipPosting(models.Model):
    LEVEL_CHOICES = (('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced'))
    NATURE_CHOICES = (('Full-Time', 'Full-Time'), ('Part-Time', 'Part-Time'), ('Remote', 'Remote'))
    
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='postings')
    track = models.ForeignKey(TrainingTrack, on_delete=models.CASCADE, related_name='postings')
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()
    location = models.CharField(max_length=255)
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES)
    nature = models.CharField(max_length=50, choices=NATURE_CHOICES)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    education_level = models.CharField(max_length=100)
    views_count = models.PositiveIntegerField(default=0)
    is_approved = models.BooleanField(default=False)
    
    # ==========================================
    # ADVISOR REQUIREMENT: Company Capacity Limit
    # ==========================================
    max_interns = models.PositiveIntegerField(
        default=3, 
        help_text="Maximum number of students allowed to be hired for this position."
    )
    # ==========================================
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} at {self.company.company_name}"

class Application(models.Model):
    # Added 'Cancelled' to the list of allowed statuses
    STATUS_CHOICES = (
        ('Pending', 'Pending'), 
        ('Shortlisted', 'Shortlisted'), 
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled')
    )
    
    internship = models.ForeignKey(InternshipPosting, on_delete=models.CASCADE, related_name='applications')
    student_name = models.CharField(max_length=255)
    university_name = models.CharField(max_length=255)
    email = models.EmailField()
    
    # 4 Mandatory Secure Document Upload Handles
    cv_file = models.FileField(upload_to='resumes/cv/')
    cpr_file = models.FileField(upload_to='resumes/cpr/')
    passport_file = models.FileField(upload_to='resumes/passport/')
    uni_id_file = models.FileField(upload_to='resumes/uni_id/')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application by {self.student_name} for {self.internship.title}"

class AttendanceRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    hours_worked = models.FloatField(default=0.0)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.hours_worked} hrs)"
    
class SupervisorEvaluation(models.Model):
    # Links directly to the Application model you already built
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='evaluation')
    
    # The 3 specific criteria, graded out of 10
    attendance_score = models.PositiveIntegerField()
    teamwork_score = models.PositiveIntegerField()
    performance_score = models.PositiveIntegerField()
    
    evaluated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Grades for {self.application.student_name}"

class CompanyReview(models.Model):
    # Links directly to the Application 
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='company_review')
    
    # 1 to 5 star rating system
    rating = models.PositiveIntegerField()
    comments = models.TextField()
    
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.application.internship.company.company_name} by {self.application.student_name}"

class WeeklyReport(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Needs Revision'),
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_reports')
    # Link directly to the active internship application
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='weekly_reports', null=True, blank=True)
    week_start_date = models.DateField()
    tasks_completed = models.TextField()
    
    # Status & Instructor Feedback
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    instructor_feedback = models.TextField(blank=True, null=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.student.username} - {self.week_start_date} ({self.status})"