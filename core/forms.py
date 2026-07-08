from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth.models import User
from .models import PakistaniAlternative, UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    display_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'How should we call you?'}))

    class Meta:
        model = User
        fields = ('username', 'display_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'


class AvatarForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('avatar',)
        widgets = {'avatar': forms.FileInput(attrs={'accept': 'image/*'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].widget.attrs['class'] = 'form-input'


class ProfileSettingsForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ('display_name',)
        widgets = {'display_name': forms.TextInput(attrs={'placeholder': 'Your display name'})}

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['email'].initial = user.email
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.email = self.cleaned_data['email']
        if commit:
            self.user.save()
            profile.save()
        return profile


class PasswordChangeForm(DjangoPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'
        self.fields['old_password'].help_text = None
        self.fields['new_password1'].help_text = None
        self.fields['new_password2'].help_text = None


class AlternativeForm(forms.ModelForm):
    class Meta:
        model = PakistaniAlternative
        fields = ('name', 'brand', 'description', 'image_url', 'website')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Product name'}),
            'brand': forms.TextInput(attrs={'placeholder': 'Brand name'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Why is this a good alternative?'}),
            'image_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'


class ModerationForm(forms.ModelForm):
    class Meta:
        model = PakistaniAlternative
        fields = ('name', 'brand', 'description', 'image_url', 'website', 'admin_notes', 'rejection_reason')
        widgets = {
            'name': forms.TextInput(),
            'brand': forms.TextInput(),
            'description': forms.Textarea(attrs={'rows': 3}),
            'image_url': forms.URLInput(),
            'website': forms.URLInput(),
            'admin_notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Internal notes (not shown to user)'}),
            'rejection_reason': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Reason shown to the submitter'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'
