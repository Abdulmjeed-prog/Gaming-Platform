from django.db import models
from accounts.models import User

class Report(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    target_type = models.CharField(max_length=50)  # review, comment, game
    target_id = models.PositiveIntegerField()

    reason = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)


class ModerationLog(models.Model):
    moderator = models.ForeignKey(User, on_delete=models.CASCADE)

    target_type = models.CharField(max_length=50)
    target_id = models.PositiveIntegerField()

    action = models.CharField(max_length=50)  # delete, ban, approve
    reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)