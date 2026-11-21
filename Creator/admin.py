from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import SavedContent, ContentPlan, Analytics

admin.site.register(SavedContent)
admin.site.register(ContentPlan)
admin.site.register(Analytics)