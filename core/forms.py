from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth import get_user_model
User = get_user_model()
from .models import PakistaniAlternative, UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'}))
    display_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'How should we call you?'}))
    security_question = forms.ChoiceField(
        choices=UserProfile.SECURITY_QUESTIONS,
        required=True,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    security_answer = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Your security answer'})
    )

    class Meta:
        model = User
        fields = ('username', 'display_name', 'email', 'password1', 'password2', 'security_question', 'security_answer')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={'placeholder': 'Enter username or email', 'autofocus': True})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'

    def clean(self):
        from django.core.cache import cache
        from django.contrib.auth import authenticate
        
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Rate limit by IP address to prevent username enumeration
            ip_address = self.request.META.get('REMOTE_ADDR', 'unknown') if self.request else 'unknown'
            lockout_key = f"login_lockout_{ip_address}"
            if cache.get(lockout_key):
                raise forms.ValidationError(
                    "Too many failed login attempts. Please try again later.",
                    code='account_locked',
                )

            # Try authenticating with username first
            user = authenticate(self.request, username=username, password=password)
            if user is None:
                # If username auth fails, try email
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(self.request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if user is None:
                # Increment failed attempts (IP-based to prevent enumeration)
                fail_key = f"login_fails_{ip_address}"
                fails = cache.get(fail_key, 0) + 1
                cache.set(fail_key, fails, 900)  # 15 minutes
                
                # Lock IP after 5 failed attempts
                if fails >= 5:
                    cache.set(lockout_key, True, 900)  # 15 minute lockout
                    raise forms.ValidationError(
                        "Too many failed login attempts. Please try again later.",
                        code='account_locked',
                    )
                
                # Generic error message - do not reveal whether username exists
                raise forms.ValidationError(
                    "Please enter a correct username/email and password.",
                    code='invalid_login',
                )
            
            # Clear failed attempts on successful login
            cache.delete(f"login_fails_{ip_address}")
            cache.delete(lockout_key)
            self.user_cache = user

        return self.cleaned_data


class AvatarForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('avatar',)
        widgets = {'avatar': forms.FileInput(attrs={'accept': 'image/*'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].widget.attrs['class'] = 'form-input'

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Validate file size (max 5MB)
            if avatar.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Image file too large. Maximum size is 5MB.')

            # Validate file extension
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            ext = avatar.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(f'Unsupported file extension. Allowed: {", ".join(allowed_extensions)}')

            # Validate content type (seek to beginning to ensure imghdr reads correctly)
            import imghdr
            avatar.seek(0)
            file_type = imghdr.what(avatar)
            if file_type not in ['jpeg', 'png', 'gif', 'webp']:
                raise forms.ValidationError('Invalid image file. Please upload a valid image.')

        return avatar


class ProfileSettingsForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'}))

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


class ForgotPasswordForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your username', 'autofocus': True})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'


class VerifySecurityForm(forms.Form):
    security_answer = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your security answer', 'autofocus': True})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'


class ResetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter new password', 'autofocus': True})
    )
    new_password2 = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'
        self.fields['new_password1'].help_text = None
        self.fields['new_password2'].help_text = None


class SecuritySettingsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('security_question', 'security_answer')
        widgets = {
            'security_question': forms.Select(attrs={'class': 'form-input', 'autocomplete': 'off'}),
            'security_answer': forms.TextInput(attrs={'placeholder': 'Your security answer', 'autocomplete': 'off'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'
        # Don't show the hashed answer in the form
        if self.instance and self.instance.security_answer:
            self.fields['security_answer'].help_text = 'Leave blank to keep current answer'
        # Clear both fields for unbound forms (GET requests) so previously
        # entered values are never repopulated on refresh.
        if not self.is_bound:
            self.initial['security_question'] = ''
            self.initial['security_answer'] = ''

    def save(self, commit=True):
        profile = super().save(commit=False)
        raw_answer = self.cleaned_data.get('security_answer', '')
        if raw_answer:
            profile.set_security_answer(raw_answer)
        if commit:
            profile.save()
        return profile


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
            'name': forms.TextInput(attrs={'placeholder': 'Alternative name'}),
            'brand': forms.TextInput(attrs={'placeholder': 'Brand name'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Why is this a good alternative?'}),
            'image_url': forms.URLInput(attrs={'placeholder': 'https://example.com/image.jpg'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://example.com'}),
            'admin_notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Internal notes (not shown to user)'}),
            'rejection_reason': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Reason shown to the submitter'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'
