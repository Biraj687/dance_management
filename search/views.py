from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from billing.models import Invoice
from packages.models import Package
from students.models import Student
from styles.models import DanceStyle
from teachers.models import Teacher


@login_required
def search(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        for student in Student.objects.filter(Q(full_name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query))[:10]:
            results.append({'type': 'student', 'name': student.full_name, 'details': f'{student.phone} - {student.status}', 'url': f'/students/{student.pk}/'})
        for teacher in Teacher.objects.filter(Q(full_name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query))[:10]:
            results.append({'type': 'teacher', 'name': teacher.full_name, 'details': teacher.email, 'url': f'/teachers/{teacher.pk}/'})
        for package in Package.objects.filter(Q(name__icontains=query) | Q(dance_style__name__icontains=query))[:10]:
            results.append({'type': 'package', 'name': package.name, 'details': str(package.dance_style), 'url': f'/packages/{package.pk}/edit/'})
        for style in DanceStyle.objects.filter(name__icontains=query)[:10]:
            results.append({'type': 'style', 'name': style.name, 'details': style.description, 'url': f'/styles/{style.pk}/edit/'})
        for invoice in Invoice.objects.filter(invoice_number__icontains=query).select_related('enrollment__student')[:10]:
            results.append({'type': 'invoice', 'name': invoice.invoice_number, 'details': invoice.enrollment.student.full_name, 'url': f'/billing/{invoice.pk}/'})
    return render(request, 'search/results.html', {'query': query, 'results': results})
