from django.db import models

# Create your models here.

from django.db import models


class SavedContent(models.Model):
    title = models.CharField(max_length=255)
    module = models.CharField(max_length=100)
    prompt = models.TextField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ContentPlan(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Planned', 'Planned'),
        ('Published', 'Published'),
    ]

    title = models.CharField(max_length=255)
    platform = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    publish_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Planned'
    )

    def __str__(self):
        return self.title


class Analytics(models.Model):
    platform = models.CharField(max_length=100)
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    followers = models.PositiveIntegerField(default=0)
    date = models.DateField()

    @property
    def engagement_rate(self):
        if self.views == 0:
            return 0

        return round(
            (self.likes + self.comments) / self.views * 100,
            2
        )

    def __str__(self):
        return self.platform