from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from billing.models import Invoice
from students.models import Enrollment
from teachers.models import Teacher
from packages.models import Package


@login_required
def dashboard_index(request):
    today = timezone.localdate()
    start = request.GET.get('start')
    end = request.GET.get('end')
    invoices = Invoice.objects.filter(
        enrollment__student__is_active=True
    ).select_related(
        'enrollment__student',
        'enrollment__dance_style_snapshot',
    )
    if start:
        invoices = invoices.filter(issued_date__gte=start)
    if end:
        invoices = invoices.filter(issued_date__lte=end)
    active_enrollments = Enrollment.objects.filter(
        is_active=True, entry_date__lte=today, exit_date__gte=today,
    )
    expiring = active_enrollments.filter(
        exit_date__lte=today + timedelta(days=7),
    )
    styles = list(
        Enrollment.objects.values('dance_style_snapshot__name')
        .annotate(enrollments=Count('id'))
        .order_by('-enrollments')[:5]
    )
    max_enrollments = max((r['enrollments'] for r in styles), default=1)
    total_revenue = invoices.aggregate(
        total=Sum('enrollment__amount_paid'),
    )['total'] or Decimal('0')

    context = {
        'today': today,
        'start_date': start or '',
        'end_date': end or '',
        'active_student_count': active_enrollments.values('student_id').distinct().count(),
        'expiring_count': expiring.values('student_id').distinct().count(),
        'total_revenue': total_revenue,
        'recent_invoices': invoices.order_by('-issued_date')[:10],
        'top_styles': [
            {
                'name': row['dance_style_snapshot__name'],
                'enrollments': row['enrollments'],
                'pct': int(row['enrollments'] / max_enrollments * 100),
            }
            for row in styles
        ],
        'active_teachers': Teacher.objects.filter(is_active=True).count(),
        'total_packages': Package.objects.filter(is_active=True).count(),
        'expiring_soon_students': expiring.select_related(
            'student', 'dance_style_snapshot',
        )[:10],
        'kpis': [
            {
                'label': 'Active students',
                'value': active_enrollments.values('student_id').distinct().count(),
                'subtitle': 'Currently enrolled',
                'link': '/students/?status=ACTIVE',
            },
            {
                'label': 'Expiring in 7 days',
                'value': expiring.values('student_id').distinct().count(),
                'subtitle': 'Renewals due soon',
                'link': '/students/?status=EXPIRING',
            },
            {
                'label': 'Active teachers',
                'value': Teacher.objects.filter(is_active=True).count(),
                'subtitle': 'Instructors on roster',
                'link': '/teachers/',
            },
            {
                'label': 'Total revenue',
                'value': f"{total_revenue:,.0f}",
                'subtitle': 'From selected period',
                'link': '/billing/',
            },
        ],
    }
    if request.headers.get('HX-Request') == 'true':
        return render(request, 'dashboard/partials/recent_invoices.html', context)
    return render(request, 'dashboard/index.html', context)


def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)
