import datetime
from django import forms
from django.core.exceptions import ValidationError
from .models import Game, GameVersion, GameKey

CURRENT_YEAR = datetime.date.today().year


class GameForm(forms.ModelForm):
    requirements_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Browser: Chrome\nRAM: 4GB\nOS: Windows 10',
        }),
        required=False,
        label='Requirements',
        help_text='One requirement per line in Key: Value format',
    )

    class Meta:
        model = Game
        fields = [
            'title',
            'genre',
            'description',
            'price',
            'publisher',
            'release_year',
            'cover',
            'play_url',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'genre': forms.CheckboxSelectMultiple(),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control'}),
            'release_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'cover': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'play_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def clean_release_year(self):
        year = self.cleaned_data.get('release_year')
        if year and (year < 1970 or year > CURRENT_YEAR + 5):
            raise ValidationError(f'Year must be between 1970 and {CURRENT_YEAR + 5}.')
        return year


class GameVersionForm(forms.ModelForm):
    class Meta:
        model = GameVersion
        fields = ['version_number', 'file', 'entry_point', 'changelog']
        widgets = {
            'version_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1.0.0'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'entry_point': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'index.html'}),
            'changelog': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file and not file.name.endswith('.zip'):
            raise ValidationError('Only .zip files are allowed.')
        return file


class GameKeyForm(forms.ModelForm):
    class Meta:
        model = GameKey
        fields = ['key']
        widgets = {
            'key': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter redeem key',
            })
        }