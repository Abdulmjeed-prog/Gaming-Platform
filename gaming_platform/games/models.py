from django.db import models
from django.utils.text import slugify


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, default="temp-slug")

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

    genre = models.ManyToManyField(
        Genre,
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



    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)

    play_count = models.PositiveIntegerField(default=0)

    is_featured = models.BooleanField(default=False)
    trending_score = models.FloatField(default=0)

    requirements = models.JSONField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['avg_rating']),
            models.Index(fields=['price']),
            models.Index(fields=['trending_score']),
        ]

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
    

    
class GameMedia(models.Model):
    MEDIA_TYPE = (
        ('image', 'Image'),
        ('video', 'Video'),
    )

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE)
    file = models.FileField(upload_to='game_media/')
    title = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)


class GameVersion(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=50)
    file = models.FileField(upload_to='game_versions/')
    entry_point = models.CharField(max_length=255)  # launch file
    changelog = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)