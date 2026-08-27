"""
Package models for pricing and duration configurations.
"""
from django.db import models
from core.models import TimeStampedModel, SoftDeleteModel


class Package(SoftDeleteModel):
    """
    Represents a pricing package for a dance style.
    """
    DURATION_UNITS = [
        ('WEEK', 'Weeks'),
        ('MONTH', 'Months'),
    ]

    name = models.CharField(
        max_length=150,
        verbose_name='Package Name'
    )
    dance_style = models.ForeignKey(
        'styles.DanceStyle',
        on_delete=models.PROTECT,
        related_name='packages',
        verbose_name='Dance Style'
    )
    duration_value = models.PositiveIntegerField(
        verbose_name='Duration Value'
    )
    duration_unit = models.CharField(
        max_length=10,
        choices=DURATION_UNITS,
        verbose_name='Duration Unit'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Price'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )

    class Meta:
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'
        ordering = ['dance_style', 'name']

    def __str__(self):
        return f"{self.name} ({self.dance_style.name})"

    def get_duration_display(self):
        """Return human-readable duration."""
        return f"{self.duration_value} {self.get_duration_unit_display()}"

    def get_active_enrollment_count(self):
        """Return count of active enrollments for this package."""
        from students.models import Enrollment
        return self.enrollments.filter(
            is_active=True
        ).count()


class PackageTimeSlot(TimeStampedModel):
    """A class time offered by a package, such as 5:00-7:00 PM."""
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='time_slots')
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['start_time']
        constraints = [models.UniqueConstraint(fields=['package', 'start_time', 'end_time'], name='unique_package_time_slot')]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'End time must be after start time.'})

    def __str__(self):
        return f'{self.start_time.strftime("%H:%M")} to {self.end_time.strftime("%H:%M")}'

    @property
    def enrolled_count(self):
        return self.enrollments.filter(is_active=True).count()