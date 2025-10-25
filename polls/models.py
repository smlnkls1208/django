import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, User
from django.dispatch import Signal
from .utilities import send_activation_notification

class AdvUser(AbstractUser):
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    is_activated = models.BooleanField(default=True, db_index=True, verbose_name="Прошёл активацию?")
    send_messages = models.BooleanField(default=True, verbose_name="Оповещать при новых комментариях?")

    class Meta(AbstractUser.Meta):
        pass

user_registrated = Signal(['instance'])

def user_registrated_dispatcher(sender, **kwargs):
    send_activation_notification(kwargs["instance"])

user_registrated.connect(user_registrated_dispatcher)

class Question(models.Model):
    title = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published', default=timezone.now)
    author = models.ForeignKey(AdvUser, on_delete=models.CASCADE)

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Вопрос')
    choice_text = models.CharField(max_length=200, verbose_name='Варианты ответа')
    votes = models.IntegerField(default=0, verbose_name='Голос')
    user = models.ForeignKey(AdvUser, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.choice_text


