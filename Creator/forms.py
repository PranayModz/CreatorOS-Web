
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import ContentPlan, Analytics


# ==========================================
# PLATFORM CHOICES
# ==========================================

PLATFORM_CHOICES = [
    ('', 'Select Platform'),
    ('YouTube', 'YouTube'),
    ('Instagram', 'Instagram'),
    ('Facebook', 'Facebook'),
    ('TikTok', 'TikTok'),
    ('LinkedIn', 'LinkedIn'),
    ('X (Twitter)', 'X (Twitter)'),
    ('Snapchat', 'Snapchat'),
    ('Threads', 'Threads'),
    ('Pinterest', 'Pinterest'),
    ('Twitch', 'Twitch'),
    ('Other', 'Other'),
]


# ==========================================
# SOCIAL MEDIA PLANNER FORM
# ==========================================

class ContentPlanForm(forms.ModelForm):

    class Meta:
        model = ContentPlan
        fields = '__all__'

        widgets = {
            'publish_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }


# ==========================================
# CREATOR ANALYTICS FORM
# ==========================================

class AnalyticsForm(forms.ModelForm):

    platform = forms.ChoiceField(
        choices=PLATFORM_CHOICES,
        label='Select Platform'
    )

    custom_platform = forms.CharField(
        required=False,
        max_length=100,
        label='Enter Platform Name',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter your platform name'
            }
        )
    )

    class Meta:
        model = Analytics

        fields = [
            'platform',
            'custom_platform',
            'views',
            'likes',
            'comments',
            'followers',
            'date',
        ]

        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        platform = cleaned_data.get('platform')

        custom_platform = cleaned_data.get(
            'custom_platform', ''
        ).strip()

        if platform == 'Other':

            if not custom_platform:

                self.add_error(
                    'custom_platform',
                    'Please enter a platform name.'
                )

            else:

                cleaned_data['platform'] = custom_platform

        return cleaned_data


# ==========================================
# USER REGISTRATION FORM
# ==========================================

class RegisterForm(UserCreationForm):

    email = forms.EmailField(required=True)

    class Meta:
        model = User

        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]

    def clean_email(self):

        email = self.cleaned_data['email'].strip().lower()

        if User.objects.filter(email__iexact=email).exists():

            raise forms.ValidationError(
                "This email is already registered."
            )

        return email
