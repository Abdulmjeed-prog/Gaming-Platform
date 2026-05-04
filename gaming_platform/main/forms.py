# forms.py
from django import forms
from .models import UploadTest

class UploadTestForm(forms.ModelForm):
    class Meta:
        model = UploadTest
        fields = ['title', 'test_file']