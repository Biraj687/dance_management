"""
Dance Style models for cataloging dance styles.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core.models import SoftDeleteModel


class DanceStyle(SoftDeleteModel):
    """
    Represents a dance style category (e.g., Salsa, Hip Hop, Classical).
    """
    name = models.CharField(
        max_length=80,
        unique=True,
        verbose_name='Style Name'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    color_tag = models.CharField(
        max_length=7,
        blank=True,
        help_text='Hex color code for UI grouping',
        verbose_name='Color Tag'
    )

    class Meta:
        verbose_name = 'Dance Style'
        verbose_name_plural = 'Dance Styles'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def package_count(self):
        """Return count of active packages for this style."""
        return self.get_package_count()

    def get_package_count(self):
        """Return count of active packages for this style."""
        return self.packages.filter(is_active=True).count()

    def clean(self):
        """Validate uniqueness against all records including soft-deleted."""
        super().clean()
        if not self.name:
            return
        qs = DanceStyle.all_objects.filter(name__iexact=self.name.strip())
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            existing = qs.first()
            if not existing.is_active:
                raise ValidationError({
                    'name': _(
                        'A deactivated style named "%(name)s" exists. '
                        'Please restore it instead of creating a duplicate.'
                    ) % {'name': self.name.strip()}
                })
            raise ValidationError({
                'name': _(
                    'A dance style with the name "%(name)s" already exists.'
                ) % {'name': self.name.strip()}
            })