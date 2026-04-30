from django.db import models
from games.models import Game
from accounts.models import DeveloperProfile

class GameAnalytics(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    date = models.DateField()

    views = models.PositiveIntegerField(default=0)
    purchases = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class DeveloperEarnings(models.Model):
    developer = models.ForeignKey(DeveloperProfile, on_delete=models.CASCADE)
    date = models.DateField()

    revenue = models.DecimalField(max_digits=10, decimal_places=2)