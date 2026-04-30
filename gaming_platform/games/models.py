from django.db import models

# Create your models here.

from django.db import models
from django.utils.text import slugify


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Game(models.Model):
    class PlatformChoices(models.TextChoices):
        PC = 'PC', 'PC'
        PS4 = 'PS4', 'PS4'
        PS5 = 'PS5', 'PS5'
        XBOX = 'XBOX', 'Xbox'
        SWITCH = 'SWITCH', 'Nintendo Switch'
        WEB = 'WEB', 'Web Browser'

    genre = models.ForeignKey(
        Genre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='games'
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    publisher = models.CharField(max_length=150)
    release_year = models.PositiveIntegerField()
    platform = models.CharField(
        max_length=20,
        choices=PlatformChoices.choices,
        default=PlatformChoices.PC
    )
    cover = models.ImageField(upload_to='games/covers/', blank=True, null=True)
    play_url = models.URLField(blank=True, null=True)
    game_zip = models.FileField(upload_to='games/zips/', blank=True, null=True)
    launch_file = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['title']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            while Game.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title