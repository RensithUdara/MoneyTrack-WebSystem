from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, UserProfile

class CustomUserCreationForm(UserCreationForm):
    """Custom user registration form"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class ProfileUpdateForm(forms.ModelForm):
    """User profile update form"""
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'profile_picture', 'date_of_birth', 'preferred_currency',
            'monthly_income', 'risk_tolerance'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'monthly_income': forms.NumberInput(attrs={'step': '0.01'}),
        }

class UserProfileForm(forms.ModelForm):
    """User profile additional information form"""
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'location', 'website', 'occupation', 'company',
            'investment_experience'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
