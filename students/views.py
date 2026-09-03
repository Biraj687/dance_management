from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from billing.models import Invoice
from billing.views import _invoice_pdf_bytes
from django.core.files.base import ContentFile
from .forms import EnrollmentForm, StudentForm
from .models import Enrollment, Student
from packages.models import Package
from teachers.models import Teacher


def _make_invoice(enrollment):
    invoice = Invoice.objects.create(
        invoice_number=Invoice.generate_number(),
        enrollment=enrollment,
        payment_method=enrollment.payment_method,
    )
    invoice.pdf_file.save(f'{invoice.invoice_number}.pdf', ContentFile(_invoice_pdf_bytes(invoice)), save=True)
    return invoice


@login_required
def student_list(request):
    students = Student.objects.prefetch_related(
        'enrollments__package', 'enrollments__teacher', 'enrollments__time_slot'
    ).order_by('full_name')
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').upper()
    teacher_id = request.GET.get('teacher', '')
    payment_status = request.GET.get('payment_status', '').upper()
    if query:
        from django.db.models import Q
        students = students.filter(Q(full_name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query))
    from django.db.models import Q
    today = timezone.localdate()
    if status == 'EXPIRING':
        students = students.filter(enrollments__is_active=True, enrollments__entry_date__lte=today, enrollments__exit_date__gte=today, enrollments__exit_date__lte=today + timedelta(days=7))
    elif status == 'ACTIVE':
        students = students.filter(enrollments__is_active=True, enrollments__entry_date__lte=today, enrollments__exit_date__gte=today)
    elif status == 'UPCOMING':
        students = students.filter(enrollments__entry_date__gt=today)
    elif status == 'EXPIRED':
        students = students.filter(enrollments__exit_date__lt=today)
    if teacher_id:
        students = students.filter(enrollments__teacher_id=teacher_id)
    if payment_status in {'PAID', 'PENDING', 'PARTIAL'}:
        students = students.filter(enrollments__payment_status=payment_status)
    students = students.distinct()
    sort = request.GET.get('sort', 'full_name')
    if sort in {'full_name', '-full_name', 'registration_date', '-registration_date'}:
        students = students.order_by(sort)
    page = Paginator(students, 25).get_page(request.GET.get('page'))
    return render(request, 'students/list.html', {
        'students': page, 'page_obj': page, 'page_title': 'Students',
        'query': query, 'status_filter': status, 'sort': sort,
        'teachers': Teacher.objects.filter(is_active=True),
        'teacher_filter': teacher_id, 'payment_filter': payment_status,
    })


@login_required
def student_create(request):
    form = StudentForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        with transaction.atomic():
            student = form.save()
            package = form.cleaned_data.get('package')
            if package:
                admission_fee = form.cleaned_data.get('admission_fee') or Decimal('1000')
                enrollment = Enrollment.objects.create(
                    student=student,
                    package=package,
                    dance_style_snapshot=package.dance_style,
                    teacher=form.cleaned_data.get('teacher'),
                    entry_date=form.cleaned_data.get('entry_date') or timezone.localdate(),
                    exit_date=form.cleaned_data.get('exit_date'),
                    total_fee=package.price + admission_fee,
                    amount_paid=form.cleaned_data.get('amount_paid') or Decimal('0'),
                    payment_status=form.cleaned_data.get('payment_status') or 'PENDING',
                    package_term=form.cleaned_data.get('package_term') or '',
                    payment_method=form.cleaned_data.get('payment_method') or '',
                    time_slot=form.cleaned_data.get('time_slot'),
                )
                enrollment.full_clean()
                invoice = _make_invoice(enrollment)
                messages.success(request, f'Student "{student.full_name}" added and enrolled. Invoice {invoice.invoice_number} created.')
                return redirect('billing:detail', pk=invoice.pk)
        messages.success(request, f'Student "{student.full_name}" created. You can enroll them later.')
        return redirect('students:detail', pk=student.pk)
    return render(request, 'students/form.html', {'form': form, 'form_action': 'students:create', 'page_title': 'Add Student'})


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student.objects.prefetch_related(
        'enrollments__package', 'enrollments__dance_style_snapshot',
        'enrollments__teacher', 'enrollments__time_slot', 'enrollments__payments'
    ), pk=pk)
    history = []
    for enrollment in student.enrollments.all():
        history.append({
            'package_name': enrollment.package.name,
            'style': enrollment.dance_style_snapshot.name if enrollment.dance_style_snapshot else '',
            'entry_date': enrollment.entry_date,
            'exit_date': enrollment.exit_date,
            'status': enrollment.status,
            'amount': enrollment.total_fee,
            'balance': enrollment.balance_due,
            'teacher': enrollment.teacher,
            'time_slot': enrollment.time_slot,
            'payments': enrollment.payments.all(),
        })
    active = student.active_enrollment
    return render(request, 'students/detail.html', {
        'student': student,
        'enrollments': history,
        'current_package': student.current_package,
        'active_enrollment': active,
        'assigned_teacher': active.teacher if active else None,
        'current_time_slot': active.time_slot if active else None,
        'current_invoice': active.invoices.order_by('-issued_date').first() if active else None,
        'page_title': student.full_name,
    })


@login_required
def student_edit(request, pk):
    student = get_object_or_404(Student.objects, pk=pk)
    form = StudentForm(request.POST or None, instance=student)
    if form.is_valid():
        form.save()
        messages.success(request, f'Student "{student.full_name}" updated successfully.')
        return redirect('students:detail', pk=pk)
    active = student.active_enrollment
    return render(request, 'students/form.html', {
        'form': form, 'student': student,
        'active_enrollment': active,
        'form_action': 'students:edit', 'form_action_kwargs': {'pk': pk},
        'page_title': 'Edit Student',
    })


@login_required
def student_enroll(request):
    student_id = request.GET.get('student_id') or request.POST.get('student_id')
    if not student_id:
        return render(request, 'students/enroll.html', {'students': Student.objects.filter(is_active=True), 'page_title': 'New Enrollment'})
    return _enroll_for_student(request, get_object_or_404(Student, pk=student_id))


@login_required
def enroll_for_student(request, pk):
    return _enroll_for_student(request, get_object_or_404(Student, pk=pk))


def _enroll_for_student(request, student):
    form = EnrollmentForm(request.POST or None, student=student)
    if form.is_valid():
        with transaction.atomic():
            enrollment = form.save()
            invoice = _make_invoice(enrollment)
        messages.success(request, f'{student.full_name} enrolled successfully. Invoice {invoice.invoice_number} created.')
        return redirect('billing:detail', pk=invoice.pk)
    return render(request, 'students/enroll.html', {'form': form, 'student': student, 'page_title': f'Enroll {student.full_name}'})


@login_required
def student_renew(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if student.active_enrollment:
        messages.error(request, 'This student still has an active package. Renewal is available after it expires.')
        return redirect('students:detail', pk=pk)
    return _enroll_for_student(request, student)
