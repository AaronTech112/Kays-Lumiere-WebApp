from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Profile

class SignUpForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, required=True, help_text='Full Name')
    email = forms.EmailField(required=True, help_text='Email Address')
    phone = forms.CharField(max_length=20, required=True, help_text='Phone Number')

    class Meta:
        model = User
        fields = ('full_name', 'email', 'phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add class to all fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'field'})
            
            # Add specific placeholders
            if field == 'full_name':
                self.fields[field].widget.attrs.update({'placeholder': 'Full Name'})
            elif field == 'email':
                self.fields[field].widget.attrs.update({'placeholder': 'Email Address'})
            elif field == 'phone':
                self.fields[field].widget.attrs.update({'placeholder': 'Phone Number'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Use email as username
        
        # Split full name
        names = self.cleaned_data['full_name'].split(' ', 1)
        user.first_name = names[0]
        if len(names) > 1:
            user.last_name = names[1]
            
        if commit:
            user.save()
            # Save phone to profile
            profile, created = Profile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data['phone']
            profile.save()
        return user

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'field', 'autofocus': True, 'placeholder': 'Email'}), 
        label='Email'
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'field', 'placeholder': 'Password'}),
    )
