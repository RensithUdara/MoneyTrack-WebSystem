from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, UserProfile
from .forms import CustomUserCreationForm, ProfileUpdateForm
import uuid

class CustomLoginView(LoginView):
    """Custom login view"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('dashboard:dashboard')

class RegisterView(CreateView):
    """User registration view"""
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Generate verification token
        user.verification_token = str(uuid.uuid4())
        user.save()
        
        # Send verification email (simplified for now)
        messages.success(
            self.request,
            'Registration successful! Please check your email to verify your account.'
        )
        
        return response

class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view"""
    model = CustomUser
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'
    
    def get_object(self):
        return self.request.user

class EditProfileView(LoginRequiredMixin, UpdateView):
    """Edit user profile"""
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user

class ChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    """Change password view"""
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:profile')
    
    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed successfully.')
        return super().form_valid(form)

def verify_email(request, token):
    """Verify email address"""
    try:
        user = CustomUser.objects.get(verification_token=token)
        user.is_verified = True
        user.verification_token = ''
        user.save()
        messages.success(request, 'Your email has been verified successfully!')
        return redirect('accounts:login')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid verification token.')
        return redirect('accounts:login')

def resend_verification(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email, is_verified=False)
            # Send verification email logic here
            messages.success(request, 'Verification email has been resent.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'No unverified account found with this email.')
    
    return render(request, 'accounts/resend_verification.html')
