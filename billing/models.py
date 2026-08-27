"""
Billing models for invoices and payments.
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import TimeStampedModel
from students.models import Enrollment


class Invoice(TimeStampedModel):
    """
    Represents an invoice for a student enrollment.
    """
    invoice_number = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Invoice Number'
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.PROTECT,
        related_name='invoices',
        verbose_name='Enrollment'
    )
    issued_date = models.DateField(
        auto_now_add=True,
        verbose_name='Issue Date'
    )
    payment_method = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Payment Method'
    )
    pdf_file = models.FileField(
        upload_to='invoices/',
        blank=True,
        null=True,
        verbose_name='PDF File'
    )

    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-issued_date']

    def __str__(self):
        return self.invoice_number

    def save(self, *args, **kwargs):
        if self.pk:
            original = Invoice.objects.get(pk=self.pk)
            if original.pdf_file != self.pdf_file:
                super().save(update_fields=['pdf_file', 'updated_at'])
                return
            raise ValidationError('Invoices are immutable and cannot be updated after creation.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Invoices cannot be deleted. Keep them for audit history.')

    @classmethod
    def generate_number(cls):
        """Generate next sequential invoice number."""
        from django.utils import timezone
        year = timezone.localdate().year
        last_invoice = cls.objects.filter(
            invoice_number__startswith=f'INV-{year}-'
        ).order_by('-invoice_number').first()

        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1

        return f'INV-{year}-{next_num:04d}'


class Payment(TimeStampedModel):
    """An immutable payment recorded against an enrollment."""
    enrollment = models.ForeignKey(Enrollment, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=[('CASH', 'Cash'), ('FONEPAY', 'Fonepay')], blank=True)
    paid_on = models.DateField(default=timezone.localdate)
    recorded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-paid_on', '-created_at']

    def __str__(self):
        return f'{self.enrollment.student.full_name} - {self.amount}'


class AuditLog(TimeStampedModel):
    """
    Tracks changes to key models for audit trail.
    """
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='User'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='Action'
    )
    model_name = models.CharField(
        max_length=50,
        verbose_name='Model'
    )
    object_id = models.PositiveIntegerField(
        verbose_name='Object ID'
    )
    change_summary = models.TextField(
        blank=True,
        verbose_name='Change Summary'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP Address'
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='User Agent'
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name='Timestamp'
    )

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} {self.model_name} #{self.object_id} by {self.user}"