from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from .models import Question, Choice
from django.template import TemplateDoesNotExist
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.template.loader import get_template
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import UpdateView
from .forms import ChangeUserInfoForm, QuestionForm, ChoiceFormSet
from .models import AdvUser
from django.contrib.auth.views import PasswordChangeView
from django.views.generic.edit import CreateView
from .forms import RegisterUserForm
from django.views.generic.base import TemplateView, View
from django.core.signing import BadSignature
from .utilities import signer
from django.views.generic import DeleteView
from django.contrib import messages


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        return Question.objects.order_by('-pub_date')


class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.object

        total_votes = sum(choice.votes for choice in question.choice_set.all())

        choices_with_percent = []
        for choice in question.choice_set.all():
            percent = round(choice.votes / total_votes * 100, 1) if total_votes > 0 else 0
            choices_with_percent.append({
                'choice': choice,
                'percent': percent
            })

        context['choices_with_percent'] = choices_with_percent
        context['total_votes'] = total_votes
        return context


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if Choice.objects.filter(question=question, user=request.user).exists():
        messages.error(request, "Вы уже голосовали в этом опросе.Результаты ниже.")
        return render(request, 'polls/detail.html', {
            'question': question,
            'already_voted': True,
            'error_message': "Вы уже голосовали."
        })
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': 'вы не сделали выбор'
        })
    else:
        selected_choice.votes += 1
        selected_choice.user = request.user
        selected_choice.save()
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))


def index(request):
    return render(request, 'polls/index.html')

def other_page(request, page):
    try:
        template = get_template('polls/' + page +'.html')
    except TemplateDoesNotExist:
        raise Http404
    return HttpResponse(template.render(request = request))

class BBLoginView(LoginView):
    template_name = 'polls/login.html'

@login_required
def profile(request):
    return render(request, 'polls/profile.html')

def logout_view(request):
    logout(request)
    return redirect('/')

class ChangeUserInfoView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = AdvUser
    template_name = 'polls/change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('polls:profile')
    success_message = "Личные данные пользователя изменены"

    def dispatch(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)

class BBPasswordChangeView(SuccessMessageMixin, LoginRequiredMixin, PasswordChangeView):
    template_name = 'polls/password_change.html'

class RegisterUserView(CreateView):
    model = AdvUser
    template_name = 'polls/register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('polls:login')

class RegisterDoneView(TemplateView):
    template_name = 'polls/register_done.html'

def user_activate(request, sign):
    try:
        username = signer.unsign(sign)
    except BadSignature:
        return render(request, 'polls/bad_signature.html')
    user = get_object_or_404(AdvUser, username=username)
    if user.is_activated:
        template = 'polls/user_is_activated.html'
    else:
        template = 'polls/activation_done.html'
        user.is_activated = True
        user.is_active = True
        user.save()
    return render(request, template)

class DeleteUserView(LoginRequiredMixin, DeleteView):
    model = AdvUser
    template_name = 'polls/delete_user.html'
    success_url = reverse_lazy('polls:index')

    def dispatch(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.add_message(request,messages.SUCCESS,"Пользователь удалён")
        return super().post(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)


class CreateQuestionView(CreateView):
    model = Question
    template_name = 'polls/register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('polls:login')

# @login_required(login_url='polls:login')
# def question_bb_add(request):
#     if request.method == 'POST':
#         form = QuestionForm(request.POST, request.FILES)
#         if form.is_valid():
#             bb = form.save()
#             formset = ChoiceFormSet(request.POST, request.FILES, instance=bb)
#             if formset.is_valid():
#                 formset.save()
#                 messages.add_message(request,messages.SUCCESS, "Вопрос добавлен")
#                 return redirect('polls:index')
#     else:
#         form = QuestionForm(initial={'author': request.user.pk})
#         formset = ChoiceFormSet()
#     context = {'form': form, 'formset': formset}
#     return render(request, 'polls/question_bb_add.html', context)


@login_required(login_url='polls:login')
def question_bb_add(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            question = form.save(commit=False)
            question.author = request.user

            formset = ChoiceFormSet(request.POST, instance=question)
            if formset.is_valid():
                question.save()
                formset.save()
                messages.success(request, "Вопрос добавлен")
                return redirect('polls:index')
    else:
        form = QuestionForm()
        formset = ChoiceFormSet()

    return render(request, 'polls/question_bb_add.html', {
        'form': form,
        'formset': formset
    })
