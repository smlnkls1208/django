from django.contrib import admin
from .models import Question, Choice
from .models import AdvUser

admin.site.register(AdvUser)


class ChoiceInLine(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInLine]


admin.site.register(Question, QuestionAdmin)
