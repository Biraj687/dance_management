import tempfile
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.dates import to_bs_input
from packages.models import Package
from teachers.models import Teacher
from .forms import EnrollmentForm
from .models import Enrollment, Student


class EnrollmentRulesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # All file uploads go to temp dir during tests
        cls.temp_media = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        import shutil
        import os
        shutil.rmtree(cls.temp_media, ignore_errors=True)
        super().tearDownClass()

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def setUp(self):
        self.package = Package.objects.create(name='Monthly Salsa', duration_value=1, duration_unit='MONTH', price=Decimal('12000'))
        self.teacher = Teacher.objects.create(full_name='Maya Thapa', phone='+9779811111111', email='maya@example.com', pay_rate=Decimal('2000'))
        self.student = Student.objects.create(full_name='Priya Sharma', phone='+9779812222222')

    def make_enrollment(self, entry, exit_date, active=True):
        return Enrollment.objects.create(student=self.student, package=self.package, teacher=self.teacher, entry_date=entry, exit_date=exit_date, total_fee=Decimal('12000'), is_active=active)

    def test_status_boundaries(self):
        today = timezone.localdate()
        self.assertEqual(self.make_enrollment(today, today).status, 'ACTIVE')
        self.assertEqual(self.make_enrollment(today + timedelta(days=1), today + timedelta(days=2), False).status, 'UPCOMING')
        self.assertEqual(self.make_enrollment(today - timedelta(days=2), today - timedelta(days=1), False).status, 'EXPIRED')

    def test_overpayment_is_rejected(self):
        enrollment = Enrollment(student=self.student, package=self.package, entry_date=timezone.localdate(), exit_date=timezone.localdate() + timedelta(days=1), total_fee=Decimal('10'), amount_paid=Decimal('11'))
        with self.assertRaises(ValidationError):
            enrollment.full_clean()

    def test_second_active_enrollment_is_rejected(self):
        today = timezone.localdate()
        self.make_enrollment(today, today)
        form = EnrollmentForm(data={'package': self.package.pk, 'teacher': self.teacher.pk, 'entry_date': today, 'exit_date': today, 'total_fee': '12000', 'amount_paid': '0', 'payment_status': 'PENDING'}, student=self.student)
        self.assertFalse(form.is_valid())
        self.assertIn('already has an active package', str(form.errors))

    def test_enrollment_requires_login(self):
        response = self.client.get(reverse('students:list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_admission_form_renders_and_saves_physical_form_fields(self):
        from .forms import StudentForm
        from django.contrib.auth import get_user_model
        self.client.force_login(get_user_model().objects.create_user(username='admission-admin', password='Strong-password-123'))
        response = self.client.get(reverse('students:create'))
        self.assertEqual(response.status_code, 200)
        for field_name in ['full_name', 'date_of_birth_bs', 'father_name', 'mother_name']:
            self.assertContains(response, f'id="id_{field_name}"')
        form = StudentForm(data={
            'full_name': 'Asha Gurung', 'phone': '+9779812345678',
            'date_of_birth_bs': '2058-03-12', 'age_at_admission': '24',
            'admission_level': 'BEGINNER', 'father_name': 'Hari Gurung',
            'is_active': 'on',
        })
        self.assertTrue(form.is_valid(), form.errors)
        student = form.save()
        self.assertEqual(student.full_name, 'Asha Gurung')

    def test_enrollment_accepts_package_term_and_payment_method(self):
        form = EnrollmentForm(data={
            'package': self.package.pk, 'teacher': self.teacher.pk,
            'entry_date': timezone.localdate(), 'exit_date': timezone.localdate() + timedelta(days=30),
            'total_fee': '12000', 'amount_paid': '12000', 'payment_status': 'PAID',
            'package_term': 'THREE_MONTH', 'payment_method': 'FONEPAY',
        }, student=self.student)
        self.assertTrue(form.is_valid(), form.errors)

    def test_student_creation_can_allocate_one_package_and_teacher(self):
        from django.contrib.auth import get_user_model
        admin = get_user_model().objects.create_user(username='create-admin', password='Strong-password-123')
        self.client.force_login(admin)
        # The admission form collects B.S. (Bikram Sambat) dates, exactly as the
        # browser would submit them, e.g. 2083-05-31.
        today = timezone.localdate()
        response = self.client.post(reverse('students:create'), {
            'full_name': 'Mina Adhikari', 'phone': '+9779815555555',
            'email': 'mina@example.com', 'is_active': 'on',
            'package': self.package.pk, 'teacher': self.teacher.pk,
            'entry_date': to_bs_input(today), 'exit_date': to_bs_input(today + timedelta(days=30)),
            'package_term': 'MONTHLY', 'payment_method': 'CASH',
            'amount_paid': '12000', 'payment_status': 'PAID',
        })
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.status_code == 200 else '')
        enrollment = Enrollment.objects.get(student__full_name='Mina Adhikari')
        self.assertEqual(enrollment.package_id, self.package.pk)
        self.assertEqual(enrollment.teacher_id, self.teacher.pk)
        self.assertEqual(enrollment.invoices.count(), 1)

    def test_student_creation_assigns_package_time_slot(self):
        from packages.models import PackageTimeSlot
        slot = PackageTimeSlot.objects.create(package=self.package, start_time='17:00', end_time='19:00')
        from django.contrib.auth import get_user_model
        self.client.force_login(get_user_model().objects.create_user(username='time-admin', password='Strong-password-123'))
        today = timezone.localdate()
        response = self.client.post(reverse('students:create'), {
            'full_name': 'Time Slot Student', 'phone': '+9779815666666', 'is_active': 'on',
            'package': self.package.pk, 'time_slot': slot.pk, 'teacher': self.teacher.pk,
            'entry_date': to_bs_input(today), 'exit_date': to_bs_input(today + timedelta(days=30)),
            'package_term': 'MONTHLY', 'payment_method': 'CASH', 'amount_paid': '0', 'payment_status': 'PENDING',
        })
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.status_code == 200 else '')
        self.assertEqual(Enrollment.objects.get(student__full_name='Time Slot Student').time_slot_id, slot.pk)
