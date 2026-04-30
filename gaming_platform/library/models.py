from django.db import models
from accounts.models import User
from games.models import Game

class UserGameLibrary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    source = models.CharField(max_length=50)  # purchase, promo, admin
    acquired_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'game')


class UserGameProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    playtime_seconds = models.BigIntegerField(default=0)
    progress_data = models.JSONField(blank=True, null=True)
    last_played = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)


class CloudSave(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    slot_name = models.CharField(max_length=100, default='default')
    save_data = models.JSONField()

    updated_at = models.DateTimeField(auto_now=True)