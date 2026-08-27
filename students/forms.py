from django import forms

from .models import Enrollment, Student
from packages.models import PackageTimeSlot


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'full_name', 'profile_photo', 'date_of_birth_bs', 'age_at_admission',
            'admission_level', 'education_qualification', 'school_college',
            'phone', 'email', 'address', 'father_name', 'father_phone',
            'mother_name', 'mother_phone', 'emergency_contact_name',
            'emergency_contact_phone', 'previous_institute', 'training_duration',
            'preferred_dance_styles', 'is_active',
        ]
        widgets = {
            'admission_level': forms.RadioSelect,
            'preferred_dance_styles': forms.CheckboxSelectMultiple,
        }

    STYLE_CHOICES = [
        ('ZUMBA', 'Zumba'), ('CULTURAL', 'Cultural'), ('LOK_NRITYA', 'Lok Nritya'),
        ('HIP_HOP', 'Hip Hop'), ('SEMI_CLASSICAL', 'Semi Classical'),
        ('BOLLYWOOD', 'Bollywood'), ('B_BOYING', 'B-Boying'), ('SALSA', 'Salsa'),
        ('AEROBICS', 'Aerobics'), ('OTHERS', 'Others'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = list(self.STYLE_CHOICES)
        try:
            from styles.models import DanceStyle
            known = {value for value, _ in choices}
            choices.extend(
                (style.name, style.name)
                for style in DanceStyle.objects.filter(is_active=True)
                if style.name.casefold() not in {value.casefold() for value in known}
                and not any(marker in style.name.casefold() for marker in ('test', 'edit', 'updated', 'msg', 'smoke'))
            )
        except Exception:
            choices = list(self.STYLE_CHOICES)
        self.fields['preferred_dance_styles'] = forms.MultipleChoiceField(
            choices=choices,
            required=False,
            widget=forms.CheckboxSelectMultiple,
            initial=self.instance.preferred_dance_styles if self.instance.pk else None,
        )
        from packages.models import Package
        from teachers.models import Teacher
        self.fields['package'] = forms.ModelChoiceField(queryset=Package.objects.filter(is_active=True), required=False, label='Package')
        self.fields['teacher'] = forms.ModelChoiceField(queryset=Teacher.objects.filter(is_active=True), required=False, label='Assigned Teacher')
        self.fields['time_slot'] = forms.ModelChoiceField(queryset=PackageTimeSlot.objects.select_related('package').filter(package__is_active=True), required=False, label='Class Time')
        self.fields['entry_date'] = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label='Entry Date')
        self.fields['exit_date'] = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label='Exit Date')
        self.fields['package_term'] = forms.ChoiceField(choices=[('', 'Select package term')] + Enrollment.PACKAGE_TERM_CHOICES, required=False, label='Package Term')
        self.fields['payment_method'] = forms.ChoiceField(choices=[('', 'Select payment method')] + Enrollment.PAYMENT_METHOD_CHOICES, required=False, label='Payment Method')
        self.fields['amount_paid'] = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2, required=False, initial=0, label='Amount Paid')
        self.fields['payment_status'] = forms.ChoiceField(choices=Enrollment.PAYMENT_STATUS_CHOICES, required=False, initial='PENDING', label='Payment Status')

    def clean_age_at_admission(self):
        age = self.cleaned_data.get('age_at_admission')
        if age is not None and not 1 <= age <= 120:
            raise forms.ValidationError('Age at admission must be between 1 and 120.')
        return age

    def clean(self):
        cleaned = super().clean()
        package = cleaned.get('package')
        time_slot = cleaned.get('time_slot')
        if package:
            entry_date = cleaned.get('entry_date')
            if not entry_date:
                from django.utils import timezone
                cleaned['entry_date'] = timezone.localdate()
            if not cleaned.get('exit_date'):
                from dateutil.relativedelta import relativedelta
                cleaned['exit_date'] = cleaned['entry_date'] + (relativedelta(weeks=package.duration_value) if package.duration_unit == 'WEEK' else relativedelta(months=package.duration_value))
            if cleaned.get('amount_paid') is not None and cleaned['amount_paid'] > package.price:
                self.add_error('amount_paid', 'Amount paid cannot exceed the package price.')
            if time_slot and time_slot.package_id != package.pk:
                self.add_error('time_slot', 'Choose a class time offered by the selected package.')
        return cleaned


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = [
            'package', 'teacher', 'entry_date', 'exit_date', 'total_fee',
            'amount_paid', 'payment_status', 'package_term', 'payment_method', 'time_slot',
        ]
        widgets = {
            'entry_date': forms.DateInput(attrs={'type': 'date'}),
            'exit_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.student = student
        self.fields['exit_date'].required = False
        self.fields['package'].queryset = self.fields['package'].queryset.filter(is_active=True)
        self.fields['teacher'].queryset = self.fields['teacher'].queryset.filter(is_active=True)
        self.fields['time_slot'].queryset = PackageTimeSlot.objects.select_related('package').filter(package__is_active=True)
        if not self.instance.pk and not self.initial.get('entry_date'):
            from django.utils import timezone
            self.initial['entry_date'] = timezone.localdate()

    def clean(self):
        cleaned = super().clean()
        package = cleaned.get('package')
        time_slot = cleaned.get('time_slot')
        if package and time_slot and time_slot.package_id != package.pk:
            self.add_error('time_slot', 'Choose a class time offered by the selected package.')
        entry_date = cleaned.get('entry_date')
        if package and not self.instance.pk:
            cleaned['total_fee'] = package.price
        if self.student:
            from django.db.models import Q
            from django.utils import timezone
            if self.student.enrollments.filter(is_active=True).exists():
                self.add_error('package', 'This student already has an active package. Renew after it expires.')
        if cleaned.get('amount_paid') is not None and cleaned.get('total_fee') is not None and cleaned['amount_paid'] > cleaned['total_fee']:
            self.add_error('amount_paid', 'Amount paid cannot exceed total fee.')
        if package and entry_date and not cleaned.get('exit_date'):
            from dateutil.relativedelta import relativedelta
            cleaned['exit_date'] = entry_date + (
                relativedelta(weeks=package.duration_value)
                if package.duration_unit == 'WEEK'
                else relativedelta(months=package.duration_value)
            )
        return cleaned

    def save(self, commit=True):
        self.instance.student = self.student or self.instance.student
        enrollment = super().save(commit=False)
        enrollment.student = self.student or enrollment.student
        enrollment.dance_style_snapshot = enrollment.package.dance_style
        if commit:
            enrollment.full_clean()
            enrollment.save()
        return enrollment