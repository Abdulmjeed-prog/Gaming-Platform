from django.db import models
from accounts.models import User
from games.models import Game


class UserGameLibrary(models.Model):
    SOURCE_CHOICES = [
        ('purchase', 'Purchase'),
        ('promo', 'Promo'),
        ('admin', 'Admin'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='library_entries')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    acquired_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'game')
        ordering = ['-acquired_at']

    def __str__(self):
        return f"{self.user} - {self.game}"


class UserGameProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='progress_entries')
    playtime_seconds = models.BigIntegerField(default=0)
    progress_data = models.JSONField(blank=True, null=True)
    last_played = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'game')

    def playtime_display(self):
        hours = self.playtime_seconds // 3600
        minutes = (self.playtime_seconds % 3600) // 60
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def __str__(self):
        return f"{self.user} - {self.game} progress"


class CloudSave(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cloud_saves')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='cloud_saves')
    slot_name = models.CharField(max_length=100, default='default')
    save_data = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'game', 'slot_name')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user} - {self.game} [{self.slot_name}]"