from django import forms
from django.utils import timezone
from decimal import Decimal

from core.forms import BSDateField
from .models import Enrollment, Student
from packages.models import PackageTimeSlot


class StudentForm(forms.ModelForm):
    """
    Used for both create and edit. On edit (instance.pk set),
    enrollment fields are excluded — package info shown read-only in the template.
    On create, enrollment fields are shown so a package can be assigned immediately.
    """
    class Meta:
        model = Student
        fields = [
            'full_name', 'date_of_birth_bs', 'age_at_admission',
            'admission_level', 'education_qualification', 'school_college',
            'phone', 'email', 'address', 'father_name', 'father_phone',
            'mother_name', 'mother_phone', 'emergency_contact_name',
            'emergency_contact_phone', 'previous_institute', 'training_duration',
            'is_active',
        ]
        widgets = {
            # Plain <select> dropdown (the model is not required, so Django
            # adds the "Select admission level" empty option automatically).
            'admission_level': forms.Select,
        }

    def __init__(self, *args, **kwargs):
        self._is_edit = kwargs.get('instance') is not None and kwargs['instance'].pk is not None
        super().__init__(*args, **kwargs)
        # Only add enrollment fields when creating a new student
        if not self._is_edit:
            from packages.models import Package
            from teachers.models import Teacher
            self.fields['package'] = forms.ModelChoiceField(
                queryset=Package.objects.filter(is_active=True),
                required=False, label='Package'
            )
            self.fields['teacher'] = forms.ModelChoiceField(
                queryset=Teacher.objects.filter(is_active=True),
                required=False, label='Assigned Teacher'
            )
            self.fields['time_slot'] = forms.ModelChoiceField(
                queryset=PackageTimeSlot.objects.select_related('package').filter(package__is_active=True),
                required=False, label='Class Time'
            )
            self.fields['entry_date'] = BSDateField(
                required=False,
                label='Entry Date (B.S.)'
            )
            self.fields['exit_date'] = BSDateField(
                required=False,
                label='Exit Date (B.S.)'
            )
            self.initial.setdefault('entry_date', timezone.localdate())
            self.fields['package_term'] = forms.ChoiceField(
                choices=[('', 'Select package term')] + Enrollment.PACKAGE_TERM_CHOICES,
                required=False, label='Package Term'
            )
            self.fields['payment_method'] = forms.ChoiceField(
                choices=[('', 'Select payment method')] + Enrollment.PAYMENT_METHOD_CHOICES,
                required=False, label='Payment Method'
            )
            self.fields['admission_fee'] = forms.DecimalField(
                min_value=0, max_digits=10, decimal_places=2,
                required=False, initial=Decimal('1000'),
                label='Admission Fee (\u0930\u0942)',
                help_text='One-time admission fee added on top of package price. Default \u0930\u0942 1000.'
            )
            self.fields['amount_paid'] = forms.DecimalField(
                min_value=0, max_digits=10, decimal_places=2,
                required=False, initial=0, label='Amount Paid'
            )
            self.fields['payment_status'] = forms.ChoiceField(
                choices=Enrollment.PAYMENT_STATUS_CHOICES,
                required=False, initial='PENDING', label='Payment Status'
            )

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
                cleaned['exit_date'] = cleaned['entry_date'] + (
                    relativedelta(weeks=package.duration_value)
                    if package.duration_unit == 'WEEK'
                    else relativedelta(months=package.duration_value)
                )
            amount_paid = cleaned.get('amount_paid') or Decimal('0')
            admission_fee = cleaned.get('admission_fee') or Decimal('1000')
            total = package.price + admission_fee
            if amount_paid > total:
                self.add_error('amount_paid', 'Amount paid cannot exceed total fee (package + admission fee).')
            if time_slot and time_slot.package_id != package.pk:
                self.add_error('time_slot', 'Choose a class time offered by the selected package.')
        return cleaned


class EnrollmentForm(forms.ModelForm):
    admission_fee = forms.DecimalField(
        min_value=0, max_digits=10, decimal_places=2,
        required=False, initial=Decimal('1000'),
        label='Admission Fee (\u0930\u0942)',
        help_text='One-time admission fee added on top of package price. Default \u0930\u0942 1000.'
    )

    class Meta:
        model = Enrollment
        fields = [
            'package', 'teacher', 'entry_date', 'exit_date', 'total_fee',
            'amount_paid', 'payment_status', 'package_term', 'payment_method', 'time_slot',
        ]

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.student = student
        self.fields['entry_date'] = BSDateField(label='Entry Date (B.S.)')
        self.fields['exit_date'] = BSDateField(required=False, label='Exit Date (B.S.)')
        self.fields['total_fee'].required = False
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
        admission_fee = cleaned.get('admission_fee') or Decimal('1000')
        if package and not self.instance.pk:
            cleaned['total_fee'] = package.price + admission_fee
        if self.student:
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
        if commit:
            enrollment.full_clean()
            enrollment.save()
        return enrollment


class TeacherAssignmentForm(forms.ModelForm):
    """Change the teacher assigned to a student's active enrollment."""

    class Meta:
        model = Enrollment
        fields = ['teacher']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from teachers.models import Teacher
        self.fields['teacher'].queryset = Teacher.objects.filter(is_active=True)
        self.fields['teacher'].required = False
        self.fields['teacher'].label = 'Assigned Teacher'