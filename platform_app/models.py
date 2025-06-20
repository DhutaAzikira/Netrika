from django.db import models
from django.contrib.auth.models import User


class Schedule(models.Model):
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = 'schedules'


class Interview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    tier = models.CharField(max_length=20, null=True, blank=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    whatsapp = models.CharField(max_length=20, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True)
    pendidikan = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    tools = models.TextField(blank=True, null=True)
    sertifikasi = models.TextField(blank=True, null=True)
    portofolio = models.CharField(max_length=255, null=True, blank=True)
    years_of_experience = models.IntegerField(null=True, blank=True)
    domisili_saat_ini = models.CharField(max_length=100, null=True, blank=True)
    pengalaman_relevan = models.TextField(blank=True, null=True)
    kekuatan = models.TextField(blank=True, null=True)
    kelemahan = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    skor_keseluruhan = models.IntegerField(blank=True, null=True)

    # The session_id from n8n can be added here if needed, or linked to the schedule

    class Meta:
        db_table = 'interviews'

    def __str__(self):
        return f"Interview for {self.user.username}"


class InterviewQuestion(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE)
    n8n_qid = models.CharField(max_length=10, null=True, blank=True)
    text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'interview_questions'

    def __str__(self):
        return self.text[:50]


class Answer(models.Model):
    question = models.ForeignKey(InterviewQuestion, on_delete=models.CASCADE)
    transcript = models.TextField(blank=True, null=True)
    audio_url = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'answers'


class Evaluation(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    score = models.IntegerField(blank=True, null=True)
    rationale = models.TextField(blank=True, null=True)
    evaluated_at = models.DateTimeField(auto_now_add=True)
    model_used = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'evaluations'


class Result(models.Model):
    # A OneToOneField with primary_key=True correctly models
    # a table where the foreign key is also the primary key.
    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, primary_key=True)
    final_score = models.IntegerField(null=True, blank=True)
    result_text = models.TextField(blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'results'