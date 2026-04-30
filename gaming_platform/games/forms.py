from django import forms
from .models import Game
class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = [
            'genre',
            'title',
            'description',
            'price',
            'publisher',
            'release_year',
            'platform',
            'cover',
            'play_url',
            'game_zip',
            'is_active',
        ]
