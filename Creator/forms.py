from django import forms
from .models import ContentPlan, Analytics


class ContentPlanForm(forms.ModelForm):
    class Meta:
        model = ContentPlan
        fields = '__all__'
        widgets = {
            'publish_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }


class AnalyticsForm(forms.ModelForm):
    class Meta:
        model = Analytics
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }