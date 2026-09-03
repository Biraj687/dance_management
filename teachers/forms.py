from django import forms

from .models import Teacher


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'full_name', 'phone', 'email', 'emergency_contact_name',
            'emergency_contact_phone', 'address',
            'pay_type', 'pay_rate', 'pay_percentage', 'is_active',
        ]

    def clean(self):
        cleaned = super().clean()
        pay_type = cleaned.get('pay_type')
        pay_rate = cleaned.get('pay_rate')
        pay_percentage = cleaned.get('pay_percentage')
        if pay_type == 'PERCENTAGE':
            if not pay_percentage or pay_percentage <= 0:
                self.add_error('pay_percentage', 'Enter a percentage greater than zero.')
            if pay_percentage and pay_percentage > 100:
                self.add_error('pay_percentage', 'Percentage cannot exceed 100.')
        else:
            if not pay_rate or pay_rate <= 0:
                self.add_error('pay_rate', 'Pay rate must be greater than zero.')
        return cleaned

    def clean_pay_rate(self):
        rate = self.cleaned_data.get('pay_rate', 0)
        # Only enforce positive for non-percentage types
        pay_type = self.data.get('pay_type')
        if pay_type != 'PERCENTAGE' and (rate is None or rate <= 0):
            raise forms.ValidationError('Pay rate must be greater than zero.')
        return rate or 0
