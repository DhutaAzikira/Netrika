from datetime import timezone, datetime

from django.db import models
from django.contrib.auth.models import User

from platform_app import apps


class UserProfiles(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    sex = models.CharField(max_length=10, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
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
    booking_code = models.CharField(max_length=20, blank=True, null=True)

    class TierPlan (models.TextChoices):
        FREE = 'Free', 'Free'
        BASIC = 'Basic', 'Basic'
        PREMIUM = 'Premium', 'Premium'

    tier = models.CharField(max_length=10, choices=TierPlan, default=TierPlan.FREE)

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
    result = models.TextField(blank=True, null=True)
    generated_at = models.DateTimeField()

    class Meta:
        db_table = 'results'
