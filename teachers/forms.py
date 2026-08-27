from django import forms

from .models import Teacher


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'full_name', 'phone', 'email', 'emergency_contact_name',
            'emergency_contact_phone', 'address', 'assigned_styles',
            'pay_type', 'pay_rate', 'max_student_capacity', 'is_active',
        ]

    def clean_pay_rate(self):
        rate = self.cleaned_data['pay_rate']
        if rate <= 0:
            raise forms.ValidationError('Pay rate must be greater than zero.')
        return rate