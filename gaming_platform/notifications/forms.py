from django import forms


class AnnouncementForm(forms.Form):
    title = forms.CharField(max_length=255)
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))