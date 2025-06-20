from django.contrib import admin
from .models import Answer, Evaluation, Interview, InterviewQuestion, Schedule, Result

# This will make each of your database tables manageable from the admin page
admin.site.register(Answer)
admin.site.register(Evaluation)
admin.site.register(Interview)
admin.site.register(InterviewQuestion)
admin.site.register(Schedule)
admin.site.register(Result)
