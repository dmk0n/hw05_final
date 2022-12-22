from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import CreationForm, ChangePassword


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class PasswordChange(CreateView):
    form_class = ChangePassword
    success_url = reverse_lazy('users:password_change_done')
    template_name = 'users/password_change_form.html'
