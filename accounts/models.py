"""
Accounts models for admin authentication.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from core.models import TimeStampedModel


class StaffProfile(TimeStampedModel):
    """
    Extended profile for staff users with role-based access.
    """
    ROLE_CHOICES = [
        ('SUPERADMIN', 'Superadmin'),
        ('STAFF', 'Staff Admin'),
    ]

    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='staff_profile',
        primary_key=True
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='STAFF',
        verbose_name='Role'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Phone')
    avatar = models.ImageField(
        upload_to='staff/avatars/',
        blank=True,
        null=True,
        verbose_name='Avatar'
    )

    class Meta:
        verbose_name = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def is_superadmin(self):
        return self.role == 'SUPERADMIN'

    @property
    def is_staff_admin(self):
        return self.role == 'STAFF'