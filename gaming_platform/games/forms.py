from django import forms
from .models import Game, GameVersion


class GameForm(forms.ModelForm):
    requirements_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Browser: Chrome\nRAM: 4GB\nOS: Windows 10'}),
        required=False,
        label='Requirements',
        help_text='One requirement per line in Key: Value format'
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
            'platform',
            'cover',
            'play_url',
            'is_active',
        ]


class GameVersionForm(forms.ModelForm):
    class Meta:
        model = GameVersion
        fields = ['version_number', 'file', 'entry_point', 'changelog']