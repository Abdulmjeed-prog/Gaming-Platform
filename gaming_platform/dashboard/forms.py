from django import forms
from games.models import Game


class AdminAddKeyGameForm(forms.ModelForm):
    keys_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8,
            'placeholder': 'Paste one key per line'
        }),
        required=False,
        help_text='Paste one game key per line.'
    )

    class Meta:
        model = Game
        fields = [
            'title',
            'description',
            'genre',
            'price',
            'platform',
            'publisher',
            'release_year',
            'cover',
            'requirements',
            'is_active',
            'is_featured',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'platform' in self.fields:
            self.fields['platform'].choices = [
                (value, label)
                for value, label in self.fields['platform'].choices
                if value != 'WEB'
            ]

        for name, field in self.fields.items():
            if name in ['is_active', 'is_featured']:
                field.widget.attrs.update({'class': 'form-check-input'})
            elif name != 'keys_text':
                field.widget.attrs.update({'class': 'form-control'})

    def clean_platform(self):
        platform = self.cleaned_data.get('platform')
        if platform == 'WEB':
            raise forms.ValidationError("You can only add key games here.")
        return platform

    def clean_keys_text(self):
        keys_text = self.cleaned_data.get('keys_text', '')
        lines = [line.strip() for line in keys_text.splitlines() if line.strip()]

        if len(lines) != len(set(lines)):
            raise forms.ValidationError("Duplicate keys found in the pasted text.")

        return lines
    

class BulkGameKeyForm(forms.Form):
    keys_text = forms.CharField(
        label='Game Keys',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Paste one key per line'
        }),
        help_text='Paste one game key per line.'
    )

    def clean_keys_text(self):
        keys_text = self.cleaned_data.get('keys_text', '')
        keys_list = [line.strip() for line in keys_text.splitlines() if line.strip()]

        if not keys_list:
            raise forms.ValidationError("Please add at least one key.")

        if len(keys_list) != len(set(keys_list)):
            raise forms.ValidationError("Duplicate keys found in the pasted text.")

        return keys_list
