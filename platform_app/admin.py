from django.contrib import admin
from .models import Answers, Evaluations, Interviews, Questions, Schedules, Results

admin.site.register(Answers)
admin.site.register(Evaluations)
admin.site.register(Interviews)
admin.site.register(Schedules)
admin.site.register(Questions)
admin.site.register(Results)

