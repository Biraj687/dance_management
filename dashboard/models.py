"""
Dashboard models for analytics KPI data.
"""
from django.db import models
from core.models import TimeStampedModel


class DashboardStats(TimeStampedModel):
    """
    Model to store dashboard KPI calculations.
    """
    total_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Total Revenue'
    )
    pending_payments = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Pending Payments'
    )
    active_students = models.PositiveIntegerField(
        default=0,
        verbose_name='Active Students'
    )
    expiring_soon = models.PositiveIntegerField(
        default=0,
        verbose_name='Expiring Soon'
    )
    active_instructors = models.PositiveIntegerField(
        default=0,
        verbose_name='Active Instructors'
    )

    class Meta:
        verbose_name = 'Dashboard Stats'
        verbose_name_plural = 'Dashboard Stats'

    def __str__(self):
        return f"Stats @ {self.created_at}"

    @classmethod
    def recalculate(cls):
        """Recalculate all dashboard stats from the database."""
        from students.models import Student
        from teachers.models import Teacher
        from billing.models import Invoice

        # Calculate total revenue from completed invoices
        total_revenue = cls._calculate_total_revenue()
        pending_payments = cls._calculate_pending_payments()
        active_students = Student.objects.filter(is_active=True).count()
        expiring_soon = cls._count_expiring_soon()
        active_instructors = Teacher.objects.filter(is_active=True).count()

        # Save or update stats
        obj, created = cls.objects.get_or_create(pk=1)
        obj.total_revenue = total_revenue
        obj.pending_payments = pending_payments
        obj.active_students = active_students
        obj.expiring_soon = expiring_soon
        obj.active_instructors = active_instructors
        obj.save()
        return obj

    @staticmethod
    def _calculate_total_revenue():
        """Calculate total revenue from all invoices."""
        from billing.models import Invoice
        total = Invoice.objects.aggregate(
            total=models.Sum('enrollment__total_fee')
        )['total'] or 0
        return total

    @staticmethod
    def _calculate_pending_payments():
        """Calculate total pending payments."""
        from billing.models import Invoice
        from students.models import Enrollment
        # Pending = invoice balance not yet paid
        pending = Enrollment.objects.filter(payment_status__in=['PENDING', 'PARTIAL']).aggregate(
            total=models.Sum('balance_due')
        )['total'] or 0
        return pending

    @staticmethod
    def _count_expiring_soon():
        """Count students whose active package expires within 7 days."""
        from django.db.models import Q, F
        from datetime import timedelta
        from students.models import Enrollment
        from django.utils import timezone

        today = timezone.localdate()
        seven_days = today + timedelta(days=7)

        expiring = Enrollment.objects.filter(
            is_active=True  # Custom manager filter
        ).filter(
            exit_date__gte=today,
            exit_date__lte=seven_days
        ).count()
        return expiring