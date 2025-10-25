from django import forms
from .models import AdvUser
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from .models import user_registrated
from .models import Question
from django.forms import inlineformset_factory
from .models import Choice


class ChangeUserInfoForm(forms.ModelForm):
    email = forms.EmailField(required=True,
                             label='дрес электронной почты')
    photo = forms.ImageField(required=True)

    class Meta:
        model = AdvUser
        fields = ('username', 'email', 'first_name', 'last_name', 'photo', 'send_messages')

class RegisterUserForm(forms.ModelForm):
    email = forms.EmailField(required=True,label="Адрес электронной почты")
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput, help_text = password_validation.password_validators_help_text_html())
    password2 = forms.CharField(label="Пароль (повторно)", widget=forms.PasswordInput, help_text = "Повторите пароль")

    def clean_password(self):
        password1 = self.cleaned_data['password1']
        if password1:
            password_validation.validate_password(password1)
        return password1

    def clean(self):
        super().clean()
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 and password2 and password1 != password2:
            errors = {'password2':ValidationError(
                "Введенные пароли не совпадают", code='password_mismatch')}
            raise ValidationError(errors)

    def save(self, commit=True):
        user = super().save(commit=True)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = True
        user.is_activated = True
        if commit:
            user.save()
        return user

    class Meta:
        model = AdvUser
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'photo', 'send_messages')

class QuestionForm(forms.ModelForm):
    photo = forms.ImageField(required=False, label='Фотография')
    class Meta:
        model = Question
        fields = ['title', 'question_text', 'photo']
        labels = {
            'title': 'Заголовок',
            'question_text': 'Описание',
            'photo': 'Фотография',
        }
        widgets = {
            'question_text': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.HiddenInput(attrs={'class': 'form-control'})
        }

ChoiceFormSet = inlineformset_factory(Question, Choice, fields=('choice_text',))

