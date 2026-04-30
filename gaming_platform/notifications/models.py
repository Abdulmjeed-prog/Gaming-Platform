from django.db import models
from accounts.models import User

class Notification(models.Model):
    TYPE_CHOICES = (
        ('purchase', 'Purchase'),
        ('comment_reply', 'Comment Reply'),
        ('game_update', 'Game Update'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)

    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)