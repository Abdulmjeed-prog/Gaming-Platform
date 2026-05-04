from django.db import models

# Create your models here.

class UploadTest(models.Model):
    title = models.CharField(max_length=100, blank=True)
    test_file = models.FileField(upload_to='upload_tests/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or self.test_file.name
