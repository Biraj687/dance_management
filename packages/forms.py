from django import forms

from .models import Package
from .models import PackageTimeSlot


class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = ['name', 'duration_value', 'duration_unit', 'price', 'description', 'is_active']

    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise forms.ValidationError('Price must be greater than zero.')
        return price

    def clean_duration_value(self):
        value = self.cleaned_data['duration_value']
        if value <= 0:
            raise forms.ValidationError('Duration must be greater than zero.')
        return value


class PackageTimeSlotForm(forms.ModelForm):
    class Meta:
        model = PackageTimeSlot
        fields = ['start_time', 'end_time']
        widgets = {'start_time': forms.TimeInput(attrs={'type': 'time'}), 'end_time': forms.TimeInput(attrs={'type': 'time'})}

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('start_time') and cleaned.get('end_time') and cleaned['end_time'] <= cleaned['start_time']:
            self.add_error('end_time', 'End time must be after start time.')
        return cleaned


PackageTimeSlotFormSet = forms.inlineformset_factory(
    Package, PackageTimeSlot, form=PackageTimeSlotForm, extra=1, can_delete=True
)