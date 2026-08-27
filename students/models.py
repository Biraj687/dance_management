"""
Student models for managing student enrollments.
"""
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from core.models import TimeStampedModel, SoftDeleteModel
from django.utils import timezone
from datetime import timedelta


class Student(SoftDeleteModel):
    """
    Represents a student enrolled in dance packages.
    """
    full_name = models.CharField(
        max_length=150,
        verbose_name='Full Name'
    )
    ADMISSION_LEVELS = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
    ]
    date_of_birth_bs = models.CharField(max_length=20, blank=True, verbose_name='Date of Birth (B.S.)')
    age_at_admission = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Age at Admission')
    admission_level = models.CharField(max_length=20, choices=ADMISSION_LEVELS, blank=True)
    education_qualification = models.CharField(max_length=180, blank=True)
    school_college = models.CharField(max_length=180, blank=True, verbose_name='Current School/College')
    phone = models.CharField(
        max_length=20,
        verbose_name='Phone'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email'
    )
    address = models.TextField(blank=True, verbose_name='Address')
    father_name = models.CharField(max_length=150, blank=True)
    father_phone = models.CharField(max_length=20, blank=True)
    mother_name = models.CharField(max_length=150, blank=True)
    mother_phone = models.CharField(max_length=20, blank=True)
    previous_institute = models.CharField(max_length=180, blank=True, verbose_name='Previous Institute')
    training_duration = models.CharField(max_length=100, blank=True, verbose_name='Training Duration')
    preferred_dance_styles = models.JSONField(default=list, blank=True)
    emergency_contact_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Emergency Contact Name'
    )
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Emergency Contact Phone'
    )
    profile_photo = models.ImageField(
        upload_to='students/photos/',
        blank=True,
        null=True,
        verbose_name='Profile Photo'
    )
    registration_date = models.DateField(
        auto_now_add=True,
        verbose_name='Registration Date'
    )

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    @property
    def active_enrollment(self):
        """Return the currently active enrollment, if any."""
        try:
            today = timezone.localdate()
            return self.enrollments.get(is_active=True, entry_date__lte=today, exit_date__gte=today)
        except Enrollment.DoesNotExist:
            return None

    @property
    def current_package(self):
        """Return the current active package, if any."""
        enrollment = self.active_enrollment
        return enrollment.package if enrollment else None

    @property
    def is_expiring_soon(self):
        """Check if student's package expires within 7 days."""
        enrollment = self.active_enrollment
        if not enrollment:
            return False
        today = timezone.localdate()
        seven_days = today + timedelta(days=7)
        return today <= enrollment.exit_date <= seven_days

    @property
    def status(self):
        enrollment = self.active_enrollment
        return enrollment.status if enrollment else 'INACTIVE'

    @property
    def balance_due(self):
        enrollment = self.active_enrollment
        return enrollment.balance_due if enrollment else 0


class Enrollment(TimeStampedModel):
    """
    Links a student to a package allocation.
    """
    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partial'),
    ]
    PACKAGE_TERM_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('THREE_MONTH', '3-Month'),
        ('SIX_MONTH', '6-Month'),
        ('YEARLY', 'Yearly'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('FONEPAY', 'Fonepay'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name='enrollments',
        verbose_name='Student'
    )
    package = models.ForeignKey(
        'packages.Package',
        on_delete=models.PROTECT,
        related_name='enrollments',
        verbose_name='Package'
    )
    dance_style_snapshot = models.ForeignKey(
        'styles.DanceStyle',
        on_delete=models.PROTECT,
        verbose_name='Dance Style'
    )
    teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enrollments',
        verbose_name='Assigned Teacher'
    )
    time_slot = models.ForeignKey(
        'packages.PackageTimeSlot', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='enrollments', verbose_name='Class Time'
    )
    entry_date = models.DateField(
        verbose_name='Entry Date'
    )
    exit_date = models.DateField(
        verbose_name='Exit Date'
    )
    total_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Total Fee (Snapshotted)'
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Amount Paid'
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING',
        verbose_name='Payment Status'
    )
    package_term = models.CharField(max_length=20, choices=PACKAGE_TERM_CHOICES, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    is_active = models.BooleanField(default=True, verbose_name='Active Slot')

    class Meta:
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        ordering = ['-entry_date']
        constraints = [
            models.UniqueConstraint(
                fields=['student'],
                condition=Q(is_active=True),
                name='one_current_enrollment_per_student',
            ),
        ]

    def __str__(self):
        return f"{self.student.full_name} - {self.package.name}"

    def clean(self):
        if self.exit_date <= self.entry_date:
            raise ValidationError({'exit_date': 'Exit date must be after entry date.'})
        if self.amount_paid > self.total_fee:
            raise ValidationError({'amount_paid': 'Amount paid cannot exceed total fee.'})
        if self.is_active and self.student_id:
            conflict = Enrollment.objects.filter(
                student_id=self.student_id, is_active=True,
            ).exclude(pk=self.pk).select_related('package').first()
            if conflict:
                raise ValidationError({
                    'student': f'This student already has the active package "{conflict.package.name}".'
                })

    @property
    def status(self):
        """Compute status based on dates."""
        today = timezone.localdate()
        if today < self.entry_date:
            return "UPCOMING"
        if today > self.exit_date:
            return "EXPIRED"
        return "ACTIVE"

    @property
    def balance_due(self):
        """Calculate remaining balance."""
        return self.total_fee - self.amount_paid

    @property
    def expiring_soon(self):
        return self.status == 'ACTIVE' and self.days_until_expiry <= 7

    @property
    def days_until_expiry(self):
        """Days until package expires."""
        today = timezone.localdate()
        if today > self.exit_date:
            return 0
        return (self.exit_date - today).days


class EnrollmentForm(models.Model):
    """Form for creating/editing enrollments."""
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='form_instance'
    )
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Created By'
    )