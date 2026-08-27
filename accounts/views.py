"""
Authentication views for the admin dashboard.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View
from .forms import LoginForm


def root_redirect(request):
    """Redirect root to login or dashboard."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('accounts:login')


@method_decorator([never_cache, csrf_protect], name='dispatch')
class LoginView(View):
    """Custom login view with studio branding."""
    template_name = 'accounts/login.html'
    form_class = LoginForm

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Welcome back!')
            next_url = request.GET.get('next', 'dashboard:index')
            return redirect(next_url)
        return render(request, self.template_name, {'form': form})


@login_required
@never_cache
def logout_view(request):
    """Logout view."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
@never_cache
def profile_view(request):
    """Staff profile view."""
    staff = getattr(request.user, 'staff_profile', None)
    return render(request, 'accounts/profile.html', {
        'staff': staff
    })