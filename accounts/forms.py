from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import CustomUser, UserProfile

class UserRegistrationForm(UserCreationForm):
    # Exclude 'admin' from registration choices - only Employee and Student can register
    USER_TYPE_CHOICES_REGISTRATION = (
        ('student', 'Student'),
        ('employee', 'Employee'),
    )
    
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES_REGISTRATION, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    department = forms.CharField(max_length=100, required=False)

    class Meta:
        model = CustomUser
        fields = (
            'username', 'first_name', 'last_name', 'email', 'user_type',
            'phone_number', 'department', 'password1', 'password2'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

            # Use field_name if label is None
            label_text = field.label if field.label else field_name.replace('_', ' ')
            field.widget.attrs['placeholder'] = f'Enter {label_text.lower()}'



class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

class UserProfileForm(forms.ModelForm):
    # --- Fields from CustomUser Model (Manually Defined) ---
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    department = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    position = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    
    # CRITICAL: This is the file input field
    profile_picture = forms.ImageField(
        required=False, 
        label='Profile Picture',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        # --- Fields from UserProfile Model (Inherited) ---
        fields = ['bio', 'skills', 'certifications'] 
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'skills': forms.TextInput(attrs={'class': 'form-control'}),
            'certifications': forms.TextInput(attrs={'class': 'form-control'}),
        }