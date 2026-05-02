from django.db import models
from accounts.models import User, DeveloperProfile


class Notification(models.Model):
    TYPE_CHOICES = (
        ('purchase', 'Purchase'),
        ('comment_reply', 'Comment Reply'),
        ('game_update', 'Game Update'),
        ('announcement', 'Announcement')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)

    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.URLField(blank=True, null=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class DeveloperAnnouncement(models.Model):
    developer = models.ForeignKey(
        DeveloperProfile,
        on_delete=models.CASCADE,
        related_name='announcements'
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title