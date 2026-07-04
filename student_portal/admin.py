from django.contrib import admin
from .models import University, Category, TrainingTrack, UserProfile, CompanyProfile, InternshipPosting, Application, AttendanceRecord

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'branch_code')
    search_fields = ('name', 'branch_code')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')

@admin.register(TrainingTrack)
class TrainingTrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_active')
    list_filter = ('category', 'is_active')

admin.site.register(UserProfile)
admin.site.register(CompanyProfile)
admin.site.register(InternshipPosting)
admin.site.register(Application)
admin.site.register(AttendanceRecord)