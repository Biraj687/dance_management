"""Regression tests for the requested studio-management fixes.

Each test pins behaviour the studio owner explicitly asked for, so a future
change cannot silently reintroduce the old behaviour:

1. Dates render as ASCII B.S. (``2083-05-31``), never Devanagari (``२०८१-०३-०५``).
2. "Expiring soon" uses a 10-day window instead of 7.
3. Admission level renders as a ``<select>`` with Beginner / Intermediate / Advanced.
4. The assigned teacher can be changed and the change is written to the audit log
   that is displayed on the student detail page.
5. Packages render without any dance-style suffix such as ``3 months (hiphop)``.
6. Choosing a package on the admission/renewal form reveals the total fee
   (package price + admission fee) and limits the Class Time dropdown to the
   class times that package actually offers.
"""

import html as html_module
import json
import re
import tempfile
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from billing.models import AuditLog
from core.dates import format_bs, format_bs_iso, to_bs_input
from packages.models import Package, PackageTimeSlot
from teachers.models import Teacher
from .models import Enrollment, Student

# Devanagari digits ० १ २ ३ ४ ५ ६ ७ ८ ९
DEVANAGARI_DIGITS = re.compile(r'[\u0966-\u096F]')


class DateFormatTests(TestCase):
    def test_format_bs_defaults_to_ascii_iso(self):
        rendered = format_bs(timezone.localdate())
        self.assertFalse(DEVANAGARI_DIGITS.search(rendered), f'Devanagari leaked: {rendered!r}')
        self.assertRegex(rendered, r'^\d{4}-\d{2}-\d{2}$')

    def test_format_bs_default_matches_explicit_iso(self):
        today = timezone.localdate()
        self.assertEqual(format_bs(today), format_bs_iso(today))

    def test_to_bs_input_is_ascii(self):
        value = to_bs_input(timezone.localdate())
        self.assertFalse(DEVANAGARI_DIGITS.search(value), f'Devanagari leaked: {value!r}')

    def test_student_detail_renders_ascii_dates(self):
        user = get_user_model().objects.create_user(username='date-admin', password='Strong-password-123')
        self.client.force_login(user)
        with override_settings(MEDIA_ROOT=tempfile.mkdtemp()):
            package = Package.objects.create(name='Monthly Salsa', duration_value=1, duration_unit='MONTH', price=Decimal('12000'))
            student = Student.objects.create(full_name='Date Student', phone='+9779810000001')
            today = timezone.localdate()
            Enrollment.objects.create(
                student=student, package=package, entry_date=today,
                exit_date=today + timedelta(days=30), total_fee=Decimal('12000'),
            )
            response = self.client.get(reverse('students:detail', args=[student.pk]))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertFalse(DEVANAGARI_DIGITS.search(body), 'Devanagari digits are still rendered.')
        self.assertIn(to_bs_input(today), body)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ExpiringWindowTests(TestCase):
    def setUp(self):
        self.package = Package.objects.create(name='Monthly Salsa', duration_value=1, duration_unit='MONTH', price=Decimal('12000'))
        self.student = Student.objects.create(full_name='Window Student', phone='+9779810000002')

    def _enroll(self, days):
        today = timezone.localdate()
        return Enrollment.objects.create(
            student=self.student, package=self.package, entry_date=today,
            exit_date=today + timedelta(days=days), total_fee=Decimal('12000'),
        )

    def test_ten_days_out_is_expiring_soon(self):
        self._enroll(10)
        self.assertTrue(self.student.is_expiring_soon)

    def test_eleven_days_out_is_not_expiring_soon(self):
        self._enroll(11)
        self.assertFalse(self.student.is_expiring_soon)


class AdmissionLevelWidgetTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='level-admin', password='Strong-password-123')
        self.client.force_login(self.user)

    def test_admission_level_is_a_select_with_the_three_options(self):
        html = self.client.get(reverse('students:create')).content.decode()
        field = re.search(r'<select[^>]*name="admission_level".*?</select>', html, re.S)
        self.assertIsNotNone(field, 'admission_level should render as a <select> dropdown.')
        for option in ('Beginner', 'Intermediate', 'Advanced'):
            self.assertIn(option, field.group(0))

    def test_admission_level_is_not_radio_buttons(self):
        html = self.client.get(reverse('students:create')).content.decode()
        self.assertNotIn('type="radio" name="admission_level"', html)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TeacherReassignmentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='teacher-admin', password='Strong-password-123')
        self.client.force_login(self.user)
        self.package = Package.objects.create(name='Monthly Salsa', duration_value=1, duration_unit='MONTH', price=Decimal('12000'))
        self.old_teacher = Teacher.objects.create(full_name='Maya Thapa', phone='+9779811111111', email='maya@example.com', pay_rate=Decimal('2000'))
        self.new_teacher = Teacher.objects.create(full_name='Bikash Rai', phone='+9779812222222', email='bikash@example.com', pay_rate=Decimal('2500'))
        self.student = Student.objects.create(full_name='Reassign Student', phone='+9779813333333')
        today = timezone.localdate()
        self.enrollment = Enrollment.objects.create(
            student=self.student, package=self.package, teacher=self.old_teacher,
            entry_date=today, exit_date=today + timedelta(days=30), total_fee=Decimal('12000'),
        )

    def test_teacher_reassignment_writes_audit_log_and_shows_it(self):
        response = self.client.post(
            reverse('students:change_teacher', args=[self.student.pk]),
            {'teacher': self.new_teacher.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.teacher_id, self.new_teacher.pk)

        log = AuditLog.objects.filter(model_name='Enrollment', object_id=self.enrollment.pk).first()
        self.assertIsNotNone(log, 'Reassigning a teacher must create an audit log entry.')
        self.assertIn('Maya Thapa', log.change_summary)
        self.assertIn('Bikash Rai', log.change_summary)

        page = self.client.get(reverse('students:detail', args=[self.student.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Bikash Rai')
        self.assertContains(page, log.change_summary)

    def test_unchanged_teacher_does_not_write_an_audit_entry(self):
        self.client.post(
            reverse('students:change_teacher', args=[self.student.pk]),
            {'teacher': self.old_teacher.pk},
        )
        self.assertEqual(AuditLog.objects.filter(model_name='Enrollment', object_id=self.enrollment.pk).count(), 0)


class PackageDisplayTests(TestCase):
    def test_package_renders_without_a_dance_style_suffix(self):
        package = Package.objects.create(name='Monthly Salsa', duration_value=3, duration_unit='MONTH', price=Decimal('30000'))
        self.assertEqual(str(package), 'Monthly Salsa')
        self.assertEqual(package.get_duration_display(), '3 Months')
        self.assertNotIn('(', str(package))
        self.assertNotIn('hiphop', str(package).lower())


def _select_data_attribute(html, field_name, attribute):
    """Pull a JSON data-* attribute off a rendered <select name="field">."""
    match = re.search(
        r'<select[^>]*name="%s"[^>]*%s="([^"]*)"' % (re.escape(field_name), re.escape(attribute)),
        html,
        re.S,
    )
    if match is None:
        return None
    return json.loads(html_module.unescape(match.group(1)))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PackageFeeAndClassTimeTests(TestCase):
    """Picking a package drives the live total fee and the class-time options."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='fee-admin', password='Strong-password-123')
        self.client.force_login(self.user)
        self.monthly = Package.objects.create(
            name='Monthly Salsa', duration_value=1, duration_unit='MONTH', price=Decimal('12000'),
        )
        self.yearly = Package.objects.create(
            name='Yearly Salsa', duration_value=12, duration_unit='MONTH', price=Decimal('60000'),
        )
        self.monthly_slot = PackageTimeSlot.objects.create(
            package=self.monthly, start_time='17:00', end_time='19:00',
        )
        self.yearly_slot = PackageTimeSlot.objects.create(
            package=self.yearly, start_time='07:00', end_time='09:00',
        )
        self.today = timezone.localdate()

    def _admission_payload(self, **overrides):
        payload = {
            'full_name': 'Fee Student', 'phone': '+9779817000000', 'is_active': 'on',
            'package': self.monthly.pk, 'time_slot': self.monthly_slot.pk,
            'admission_fee': '1000',
            'entry_date': to_bs_input(self.today),
            'exit_date': to_bs_input(self.today + timedelta(days=30)),
            'amount_paid': '0', 'payment_status': 'PENDING',
        }
        payload.update(overrides)
        return payload

    def test_package_select_exposes_prices_for_the_live_total(self):
        html = self.client.get(reverse('students:create')).content.decode()
        info = _select_data_attribute(html, 'package', 'data-package-info')
        self.assertIsNotNone(info, 'The package <select> must carry data-package-info JSON.')
        self.assertEqual(info[str(self.monthly.pk)]['price'], '12000.00')
        self.assertEqual(info[str(self.yearly.pk)]['price'], '60000.00')
        self.assertEqual(info[str(self.monthly.pk)]['name'], 'Monthly Salsa')
        # The live summary box the script writes into must be on the page.
        self.assertIn('data-fee-total', html)
        self.assertIn('id="id_admission_fee"', html)

    def test_time_slot_map_lists_only_the_selected_packages_times(self):
        html = self.client.get(reverse('students:create')).content.decode()
        slot_map = _select_data_attribute(html, 'time_slot', 'data-slot-map')
        self.assertIsNotNone(slot_map, 'The class-time <select> must carry data-slot-map JSON.')
        self.assertEqual(
            [slot['value'] for slot in slot_map[str(self.monthly.pk)]],
            [str(self.monthly_slot.pk)],
        )
        self.assertEqual(
            [slot['value'] for slot in slot_map[str(self.yearly.pk)]],
            [str(self.yearly_slot.pk)],
        )
        self.assertNotEqual(slot_map[str(self.monthly.pk)], slot_map[str(self.yearly.pk)])

    def test_admission_form_renders_the_live_fee_summary(self):
        html = self.client.get(reverse('students:create')).content.decode()
        self.assertIn('id="fee-summary"', html)
        self.assertIn('Total payable', html)

    def test_total_fee_is_auto_calculated_from_package_plus_admission_fee(self):
        response = self.client.post(reverse('students:create'), self._admission_payload())
        self.assertEqual(
            response.status_code, 302,
            response.context['form'].errors if response.status_code == 200 else '',
        )
        enrollment = Enrollment.objects.get(student__full_name='Fee Student')
        self.assertEqual(enrollment.total_fee, Decimal('13000'))
        self.assertEqual(enrollment.time_slot_id, self.monthly_slot.pk)

    def test_total_fee_uses_the_chosen_package_price(self):
        response = self.client.post(
            reverse('students:create'),
            self._admission_payload(
                full_name='Yearly Student',
                package=self.yearly.pk,
                time_slot=self.yearly_slot.pk,
                admission_fee='2000',
            ),
        )
        self.assertEqual(
            response.status_code, 302,
            response.context['form'].errors if response.status_code == 200 else '',
        )
        enrollment = Enrollment.objects.get(student__full_name='Yearly Student')
        self.assertEqual(enrollment.total_fee, Decimal('62000'))

    def test_a_slot_from_another_package_is_rejected(self):
        response = self.client.post(
            reverse('students:create'),
            self._admission_payload(
                full_name='Mismatch Student', time_slot=self.yearly_slot.pk,
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('time_slot', response.context['form'].errors)
        self.assertFalse(Student.objects.filter(full_name='Mismatch Student').exists())
