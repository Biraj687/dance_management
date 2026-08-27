"""
Forms for Dance Style CRUD operations.
"""
from django import forms
from .models import DanceStyle


class DanceStyleForm(forms.ModelForm):
    """
    ModelForm for DanceStyle with name uniqueness validation.
    Uses all_objects manager to check against soft-deleted records too.
    """
    
    class Meta:
        model = DanceStyle
        fields = ['name', 'description', 'color_tag', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg bg-bg-base border border-border-hairline text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-accent-gold focus:border-transparent transition-all',
                'placeholder': 'e.g. Salsa',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg bg-bg-base border border-border-hairline text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-accent-gold focus:border-transparent transition-all',
                'placeholder': 'Brief description of this dance style...',
                'rows': 3,
            }),
            'color_tag': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg bg-bg-base border border-border-hairline text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-accent-gold focus:border-transparent transition-all',
                'placeholder': '#F3A232',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-border-hairline text-accent-gold focus:ring-accent-gold',
            }),
        }
        labels = {
            'name': 'Style Name *',
            'description': 'Description',
            'color_tag': 'Color Tag (Hex)',
            'is_active': 'Active',
        }
        help_texts = {
            'color_tag': 'Hex color code for UI grouping (e.g., #F3A232)',
        }
    
    def clean_name(self):
        """Validate name uniqueness against all records including soft-deleted."""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            return name
        
        qs = DanceStyle.all_objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            existing = qs.first()
            if not existing.is_active:
                raise forms.ValidationError(
                    f'A deactivated style named "{name}" exists. '
                    'Please restore it instead of creating a duplicate.'
                )
            raise forms.ValidationError(
                f'A dance style with the name "{name}" already exists.'
            )
        return name