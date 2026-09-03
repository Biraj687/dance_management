import csv
from datetime import timedelta
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.core.files.base import ContentFile

from .forms import PaymentForm
from .models import AuditLog, Invoice, Payment
from students.models import Enrollment, Student
from teachers.models import Teacher


def _invoices(request):
    invoices = Invoice.objects.select_related(
        'enrollment__student', 'enrollment__package', 'enrollment__dance_style_snapshot'
    )
    status = request.GET.get('status', '').upper()
    if status in {'PAID', 'PENDING', 'PARTIAL'}:
        invoices = invoices.filter(enrollment__payment_status=status)
    query = request.GET.get('q', '').strip()
    if query:
        from django.db.models import Q
        invoices = invoices.filter(
            Q(invoice_number__icontains=query) |
            Q(enrollment__student__full_name__icontains=query) |
            Q(enrollment__package__name__icontains=query)
        )
    return invoices


@login_required
def invoice_list(request):
    page = Paginator(_invoices(request), 25).get_page(request.GET.get('page'))
    return render(request, 'billing/list.html', {'invoices': page, 'page_obj': page, 'page_title': 'Invoices'})


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(_invoices(request), pk=pk)
    payment_form = PaymentForm(enrollment=invoice.enrollment)
    return render(request, 'billing/detail.html', {'invoice': invoice, 'payment_form': payment_form, 'payments': invoice.enrollment.payments.all(), 'page_title': invoice.invoice_number})


@login_required
def payment_create(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('enrollment'), pk=pk)
    form = PaymentForm(request.POST or None, enrollment=invoice.enrollment)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            payment = form.save(commit=False)
            payment.enrollment = invoice.enrollment
            payment.recorded_by = request.user
            payment.save()
            enrollment = invoice.enrollment
            enrollment.amount_paid += payment.amount
            enrollment.payment_status = 'PAID' if enrollment.balance_due == 0 else 'PARTIAL'
            enrollment.save(update_fields=['amount_paid', 'payment_status', 'updated_at'])
            AuditLog.objects.create(user=request.user, action='UPDATE', model_name='Enrollment', object_id=enrollment.pk, change_summary=f'Payment of {payment.amount} recorded')
        messages.success(request, f'Payment recorded for {invoice.invoice_number}.')
        return redirect('billing:detail', pk=invoice.pk)
    return render(request, 'billing/payment_form.html', {'invoice': invoice, 'form': form, 'page_title': 'Record Payment'})


@login_required
def invoice_download(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('enrollment__student', 'enrollment__package', 'enrollment__dance_style_snapshot'), pk=pk)
    if not invoice.pdf_file:
        content = _invoice_pdf_bytes(invoice)
        invoice.pdf_file.save(f'{invoice.invoice_number}.pdf', ContentFile(content), save=True)
    response = HttpResponse(invoice.pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
    return response


def _csv_response(filename, headers, rows):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    return response


def _filtered_students(request):
    qs = Student.objects.prefetch_related('enrollments__package')
    query = request.GET.get('q', '').strip()
    if query:
        from django.db.models import Q
        qs = qs.filter(Q(full_name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query))
    today = timezone.localdate()
    status = request.GET.get('status', '').upper()
    if status == 'ACTIVE':
        qs = qs.filter(enrollments__is_active=True, enrollments__entry_date__lte=today, enrollments__exit_date__gte=today)
    elif status == 'UPCOMING':
        qs = qs.filter(enrollments__entry_date__gt=today)
    elif status == 'EXPIRED':
        qs = qs.filter(enrollments__exit_date__lt=today)
    elif status == 'EXPIRING':
        qs = qs.filter(enrollments__is_active=True, enrollments__entry_date__lte=today, enrollments__exit_date__gte=today, enrollments__exit_date__lte=today + timedelta(days=7))
    if request.GET.get('style'):
        qs = qs.filter(enrollments__dance_style_snapshot_id=request.GET['style'])
    if request.GET.get('teacher'):
        qs = qs.filter(enrollments__teacher_id=request.GET['teacher'])
    if request.GET.get('payment_status', '').upper() in {'PAID', 'PENDING', 'PARTIAL'}:
        qs = qs.filter(enrollments__payment_status=request.GET['payment_status'].upper())
    return qs.distinct()


@login_required
def export_students_csv(request):
    qs = _filtered_students(request)
    rows = [(s.full_name, s.phone, s.email, s.status, s.balance_due) for s in qs]
    return _csv_response('students.csv', ['Student', 'Phone', 'Email', 'Status', 'Balance Due'], rows)


@login_required
def export_teachers_csv(request):
    qs = Teacher.objects.prefetch_related('assigned_styles')
    rows = [(t.full_name, t.phone, t.email, ', '.join(s.name for s in t.assigned_styles.all()), t.active_assigned_student_count) for t in qs]
    return _csv_response('teachers.csv', ['Teacher', 'Phone', 'Email', 'Styles', 'Active Students'], rows)


@login_required
def export_ledger_csv(request):
    rows = []
    for invoice in _invoices(request):
        enrollment = invoice.enrollment
        rows.append((invoice.invoice_number, enrollment.student.full_name, enrollment.total_fee, enrollment.amount_paid, enrollment.balance_due, enrollment.payment_status, invoice.issued_date))
    return _csv_response('ledger.csv', ['Invoice', 'Student', 'Total', 'Paid', 'Balance', 'Status', 'Issued'], rows)


@login_required
def export_students_pdf(request):
    return _pdf_response('Students', [(s.full_name, s.phone, s.status) for s in _filtered_students(request)])


@login_required
def export_teachers_pdf(request):
    return _pdf_response('Teachers', [(t.full_name, t.phone, t.email) for t in Teacher.objects.all()])


@login_required
def export_ledger_pdf(request):
    return _pdf_response('Financial Ledger', [(i.invoice_number, i.enrollment.student.full_name, i.enrollment.total_fee) for i in _invoices(request)])


def _pdf_response(title, rows):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(title)
    pdf.setFont('Helvetica-Bold', 18)
    pdf.drawString(48, 800, title)
    pdf.setFont('Helvetica', 10)
    y = 770
    for row in rows:
        pdf.drawString(48, y, ' | '.join(str(value) for value in row))
        y -= 18
        if y < 48:
            pdf.showPage()
            y = 800
    pdf.save()
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{title.lower().replace(" ", "_")}.pdf"'
    return response


def _invoice_pdf_bytes(invoice):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    enrollment = invoice.enrollment
    pdf.setTitle(invoice.invoice_number)
    pdf.setFont('Helvetica-Bold', 20)
    pdf.drawString(48, 800, invoice.invoice_number)
    pdf.setFont('Helvetica', 11)
    lines = [
        f'Student: {enrollment.student.full_name}',
        f'Package: {enrollment.package.name} ({enrollment.dance_style_snapshot.name})',
        f'Period: {enrollment.entry_date} to {enrollment.exit_date}',
        f'Total: {enrollment.total_fee}',
        f'Paid: {enrollment.amount_paid}',
        f'Balance due: {enrollment.balance_due}',
    ]
    for payment in enrollment.payments.order_by('paid_on', 'created_at'):
        lines.append(f'Payment: {payment.paid_on} | {payment.get_payment_method_display() or "Unspecified"} | {payment.amount}')
    for index, line in enumerate(lines):
        pdf.drawString(48, 760 - index * 22, line)
    pdf.save()
    return buffer.getvalue()
