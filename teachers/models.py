"""
Teacher models for managing dance instructors.
"""
from django.db import models
from django.utils import timezone
from core.models import TimeStampedModel, SoftDeleteModel


class Teacher(SoftDeleteModel):
    """
    Represents a dance teacher/instructor.
    """
    full_name = models.CharField(
        max_length=150,
        verbose_name='Full Name'
    )
    phone = models.CharField(
        max_length=20,
        verbose_name='Phone'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Email'
    )
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
    address = models.TextField(
        blank=True,
        verbose_name='Address'
    )
    pay_type = models.CharField(
        max_length=10,
        choices=[
            ('HOURLY', 'Hourly'),
            ('MONTHLY', 'Monthly'),
            ('PERCENTAGE', 'Percentage of Fee'),
        ],
        default='HOURLY',
        verbose_name='Pay Type'
    )
    pay_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Pay Rate'
    )
    pay_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Pay Percentage (%)',
        help_text='Percentage of total student fees paid to this teacher (e.g. 15 = 15%)'
    )

    class Meta:
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    @property
    def is_active_with_capacity(self):
        """Check if teacher is active (no capacity limit now)."""
        return self.is_active

    @property
    def active_assigned_student_count(self):
        """Count of students currently assigned to this teacher."""
        today = timezone.localdate()
        return self.enrollments.filter(is_active=True, entry_date__lte=today, exit_date__gte=today).count()

    @property
    def total_historical_students(self):
        """Count of all students ever assigned to this teacher."""
        return self.enrollments.count()

    @property
    def monthly_wage_estimate(self):
        """Estimate of monthly wage based on pay type/rate."""
        if self.pay_type == 'HOURLY':
            return self.pay_rate * 160  # Assuming 40 hours/week
        elif self.pay_type == 'MONTHLY':
            return self.pay_rate
        elif self.pay_type == 'PERCENTAGE':
            # Sum of active student fees × percentage
            today = timezone.localdate()
            active = self.enrollments.filter(is_active=True, entry_date__lte=today, exit_date__gte=today).select_related('package')
            total_fees = sum(e.total_fee for e in active)
            return total_fees * (self.pay_percentage / 100)
        return 0


class TeacherAvailability(TimeStampedModel):
    """A recurring weekly availability slot for a teacher."""
    DAYS = [(index, day) for index, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])]
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.PositiveSmallIntegerField(choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day_of_week', 'start_time']
        constraints = [models.UniqueConstraint(fields=['teacher', 'day_of_week', 'start_time', 'end_time'], name='unique_teacher_availability_slot')]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})