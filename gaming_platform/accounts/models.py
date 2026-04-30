from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROLE_CHOICES = (
        ('player', 'Player'),
        ('developer', 'Developer'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='player')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="images/avatars/", default="images/avatars/default_avatar.jpg")

    def __str__(self):
        return f"Profile {self.user.username}"

    
class DeveloperProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name
    
    
class FollowDeveloper(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    developer = models.ForeignKey(DeveloperProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'developer')
