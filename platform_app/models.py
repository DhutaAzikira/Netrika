from datetime import timezone, datetime

from django.db import models
from django.contrib.auth.models import User

from platform_app import apps


class UserProfiles(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    profile_picture = models.TextField(blank=True, null=True, help_text="URL to the profile picture")
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_profiles'


class Schedules(models.Model):
    id = models.BigAutoField(primary_key=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    class Meta:
        db_table = 'schedules'


class Interviews(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_profile = models.ForeignKey(UserProfiles, on_delete=models.DO_NOTHING, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    schedule = models.ForeignKey(Schedules, on_delete=models.DO_NOTHING, blank=True, null=True)
    booking_code = models.CharField(max_length=25, blank=True, null=True)
    package = models.ForeignKey('admin_app.Packages', on_delete=models.DO_NOTHING, blank=True, null=True)

    class StatusField(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        SCHEDULED = 'Scheduled', 'Scheduled'
        COMPLETED = 'Completed', 'Completed'
        CANCELLED = 'Cancelled', 'Cancelled'
    status = models.CharField(max_length=10, choices=StatusField, default=StatusField.PENDING)

    class JobLevel(models.TextChoices):
        ENTRY = 'Entry', 'Entry'
        MID = 'Mid', 'Mid'
        SENIOR = 'Senior', 'Senior'
        LEAD = 'Lead', 'Lead'
        MANAGER = 'Manager', 'Manager'

    tingkatan = models.CharField(max_length=10, choices=JobLevel, default=JobLevel.ENTRY)

    class InterviewType(models.TextChoices):
        TECHNICAL = 'Technical', 'Technical'
        HR = 'HR', 'HR'
        DESIGN = 'Design', 'Design'
        MANAGEMENT = 'Management', 'Management'
        OTHER = 'Other', 'Other'

    jenis_wawancara = models.CharField(max_length=20, choices=InterviewType, default=InterviewType.TECHNICAL)

    posisi = models.CharField(max_length=100, blank=True, null=True)
    industri = models.CharField(max_length=100, blank=True, null=True)
    nama_perusahaan = models.CharField(max_length=100, blank=True, null=True)
    detail_pekerjaan = models.TextField(blank=True, null=True)

    skor_keseluruhan = models.IntegerField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)

    domisili_saat_ini = models.CharField(max_length=100, blank=True, null=True)
    kekuatan = models.TextField(blank=True, null=True)
    kelemahan = models.TextField(blank=True, null=True)
    tools = models.TextField(blank=True, null=True)
    pendidikan = models.TextField(blank=True, null=True)
    pengalaman_relevan = models.TextField(blank=True, null=True)
    portofolio = models.TextField(blank=True, null=True)
    sertifikasi = models.TextField(blank=True, null=True)
    years_of_experience = models.IntegerField(blank=True, null=True)


    class Meta:
        db_table = 'interviews'


class Questions(models.Model):
    id = models.BigAutoField(primary_key=True)
    interview = models.ForeignKey(Interviews, on_delete=models.DO_NOTHING)
    n8n_id = models.CharField(max_length=10, blank=True, null=True)
    question = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'questions'


class Answers(models.Model):
    id = models.BigAutoField(primary_key=True)
    question = models.ForeignKey(Questions, on_delete=models.DO_NOTHING)
    answer = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField()

    class Meta:
        db_table = 'answers'


class Evaluations(models.Model):
    id = models.BigAutoField(primary_key=True)
    answer = models.ForeignKey(Answers, on_delete=models.DO_NOTHING)
    score = models.IntegerField(blank=True, null=True)
    rationale = models.TextField(blank=True, null=True)
    evaluated_at = models.DateTimeField()

    class Meta:
        db_table = 'evaluations'


class Results(models.Model):
    interview = models.OneToOneField(Interviews, on_delete=models.DO_NOTHING, primary_key=True)
    final_score = models.IntegerField(blank=True, null=True)
    final_summary = models.TextField(blank=True, null=True)
    recommendation = models.TextField(blank=True, null=True)
    strengths = models.TextField(blank=True, null=True)
    gaps = models.TextField(blank=True, null=True)
    communication_skills = models.TextField(blank=True, null=True)
    cognitive_insights = models.TextField(blank=True, null=True)
    multiple_faces = models.CharField(max_length=15, blank=True, null=True)
    eye_contact = models.CharField(max_length=15, blank=True, null=True)
    face_visibility = models.CharField(max_length=15, blank=True, null=True)
    general_expression = models.CharField(max_length=15, blank=True, null=True)
    camera_quality = models.CharField(max_length=15, blank=True, null=True)
    camera_perspective = models.CharField(max_length=15, blank=True, null=True)

    generated_at = models.DateTimeField()


    class Meta:
        db_table = 'results'

class CameraAnalysis(models.Model):
    id = models.BigAutoField(primary_key=True)
    interview = models.ForeignKey(Interviews, on_delete=models.CASCADE)
    multiple_faces = models.CharField(max_length=15, blank=True, null=True)
    eye_contact = models.CharField(max_length=15, blank=True, null=True)
    face_visibility = models.CharField(max_length=15, blank=True, null=True)
    general_expression = models.CharField(max_length=15, blank=True, null=True)
    camera_quality = models.CharField(max_length=15, blank=True, null=True)
    camera_perspective = models.CharField(max_length=15, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'camera_analysis'


class CVScreeningReport(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Personal and Position Info
    full_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    score = models.IntegerField()

    grammar = models.JSONField(default='', blank=True)
    score_justification = models.TextField(default='', blank=True)

    # Sub-scores
    format_and_structure_score = models.IntegerField()
    suitability_score = models.IntegerField()
    experiences_score = models.IntegerField()

    # Score Breakdown
    profile_summary_score = models.IntegerField()
    work_experience_score = models.IntegerField()
    education_score = models.IntegerField()
    skills_score = models.IntegerField()
    certifications_score = models.IntegerField()
    projects_score = models.IntegerField()
    achievements_score = models.IntegerField()

    summary = models.TextField(default='', blank=True)
    # SWOT Analysis
    strengths = models.JSONField()
    weaknesses = models.JSONField()
    opportunities = models.JSONField()
    threats = models.JSONField()

    # Revisions/Recommendations
    revisions = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cv_screening_reports'