from django import forms
from games.models import Game, Genre


from django import forms
from games.models import Game


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(file, initial) for file in data]
        return single_file_clean(data, initial)


class AdminAddKeyGameForm(forms.ModelForm):
    genre = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

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
            if name == 'genre':
                continue

            css_class = 'field-input'
            if isinstance(field.widget, forms.Select):
                css_class = 'field-select'
            elif isinstance(field.widget, forms.Textarea):
                css_class = 'field-textarea'

            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} {css_class}'.strip()

    def clean_platform(self):
        platform = self.cleaned_data.get('platform')
        if platform == 'WEB':
            raise forms.ValidationError("WEB platform is not allowed here.")
        return platform

    def clean_keys_text(self):
        keys_text = self.cleaned_data.get('keys_text', '')
        keys_list = [line.strip() for line in keys_text.splitlines() if line.strip()]

        if len(keys_list) != len(set(keys_list)):
            raise forms.ValidationError("Duplicate keys found in pasted text.")

        return keys_list
    
    
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['keys_text'].widget.attrs.update({
            'class': 'field-textarea',
            'rows': 12,
            'placeholder': 'ABC-123-XYZ\nDEF-456-QWE\nGAME-KEY-001'
        })


    def clean_keys_text(self):
        keys_text = self.cleaned_data.get('keys_text', '')
        keys_list = [line.strip() for line in keys_text.splitlines() if line.strip()]

        if not keys_list:
            raise forms.ValidationError("Please add at least one key.")

        if len(keys_list) != len(set(keys_list)):
            raise forms.ValidationError("Duplicate keys found in the pasted text.")

        return keys_list
