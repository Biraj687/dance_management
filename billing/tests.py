import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.dates import to_bs_input
from packages.models import Package
from students.models import Enrollment, Student


class ExportTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_media = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.temp_media, ignore_errors=True)
        super().tearDownClass()

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin@example.com', password='Strong-password-123')
        self.client.force_login(self.user)
        self.package = Package.objects.create(name='Salsa Monthly', duration_value=1, duration_unit='MONTH', price=Decimal('12000'))
        Student.objects.create(full_name='Priya Sharma', phone='+9779811111111')
        Student.objects.create(full_name='Rahul Verma', phone='+9779812222222')

    def test_student_csv_export_contains_filtered_rows(self):
        response = self.client.get(reverse('billing:export_students_csv'), {'q': 'Priya'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode().count('Priya Sharma'), 1)
        self.assertNotIn('Rahul Verma', response.content.decode())

    def test_student_pdf_export_uses_filters(self):
        response = self.client.get(reverse('billing:export_students_pdf'), {'q': 'Priya'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertNotIn('Rahul Verma', response.content.decode('latin-1'))

    def test_payment_updates_enrollment_and_creates_history(self):
        from datetime import timedelta
        today = timezone.localdate()
        enrollment = Enrollment.objects.create(
            student=Student.objects.get(full_name='Priya Sharma'), package=self.package,
            entry_date=today,
            exit_date=today + timedelta(days=30), total_fee=Decimal('12000'),
            amount_paid=Decimal('2000'), payment_status='PARTIAL',
        )
        invoice = enrollment.invoices.create(invoice_number='INV-TEST-0001')
        # "paid_on" is a B.S. date field, so submit it the way the browser does.
        response = self.client.post(reverse('billing:payment', args=[invoice.pk]), {'amount': '10000', 'payment_method': 'Cash', 'paid_on': to_bs_input(today)})
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.status_code == 200 else '')
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.amount_paid, Decimal('12000'))
        self.assertEqual(enrollment.balance_due, Decimal('0'))
        self.assertEqual(enrollment.payment_status, 'PAID')
        self.assertEqual(enrollment.payments.count(), 1)
