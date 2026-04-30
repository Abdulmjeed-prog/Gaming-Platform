from django.db import models
from accounts.models import User
from games.models import Game

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()

    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'game')


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    content = models.TextField()
    is_approved = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)