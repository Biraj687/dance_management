"""
Management command to seed demo data for development and testing.
"""
from django.core.management.base import BaseCommand
from packages.models import Package, PackageTimeSlot
from teachers.models import Teacher
from students.models import Student, Enrollment
from billing.models import Invoice, Payment
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed demo packages, teachers, students and enrollments'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        packages_data = [
            {'name': 'Beginner 1 Month', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 12000, 'description': 'Basic steps and turns for beginners'},
            {'name': 'Intermediate 1 Month', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 15000, 'description': 'Intermediate patterns and styling'},
            {'name': 'Advanced 3 Months', 'duration_value': 3, 'duration_unit': 'MONTH', 'price': 40000, 'description': 'Advanced techniques and performance prep'},
            {'name': 'Foundations 1 Month', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 10000, 'description': 'Basic grooves, isolations, and freestyle'},
            {'name': 'Choreography 1 Month', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 13000, 'description': 'Learn trending choreographies'},
            {'name': 'Intensive 2 Months', 'duration_value': 2, 'duration_unit': 'MONTH', 'price': 22000, 'description': 'Comprehensive dance training'},
            {'name': 'Basics 1 Month', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 14000, 'description': 'Fundamental positions and barre work'},
            {'name': 'Flow 1 Month', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 14000, 'description': 'Choreography and emotional expression'},
            {'name': 'Compositions 2 Months', 'duration_value': 2, 'duration_unit': 'MONTH', 'price': 20000, 'description': 'Complex compositions and expression'},
            {'name': 'Social Dance 2 Months', 'duration_value': 2, 'duration_unit': 'MONTH', 'price': 25000, 'description': 'Social dance preparation and etiquette'},
        ]

        for pkg_data in packages_data:
            package, created = Package.all_objects.get_or_create(
                name=pkg_data['name'],
                defaults={
                    'duration_value': pkg_data['duration_value'],
                    'duration_unit': pkg_data['duration_unit'],
                    'price': pkg_data['price'],
                    'description': pkg_data['description'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'  Created package: {package.name}')
            elif not package.is_active:
                package.is_active = True
                package.deleted_at = None
                package.duration_value = pkg_data['duration_value']
                package.duration_unit = pkg_data['duration_unit']
                package.price = pkg_data['price']
                package.description = pkg_data['description']
                package.save(update_fields=['is_active', 'deleted_at', 'duration_value', 'duration_unit', 'price', 'description'])
                self.stdout.write(f'  Restored package: {package.name}')
            else:
                self.stdout.write(f'  Package exists: {package.name}')
            for start, end in [('17:00', '19:00'), ('20:00', '21:00')]:
                PackageTimeSlot.objects.get_or_create(package=package, start_time=start, end_time=end)

        teachers_data = [
            ('Maya Thapa', '+9779811111111', 'maya@dance.example', Decimal('2500')),
            ('Rohan Singh', '+9779812222222', 'rohan@dance.example', Decimal('75000')),
            ('Sita Sharma', '+9779813333333', 'sita@dance.example', Decimal('2200')),
            ('Aarav Gurung', '+9779814444444', 'aarav@dance.example', Decimal('2000')),
        ]
        teachers = []
        for name, phone, email, rate in teachers_data:
            teacher, _ = Teacher.objects.get_or_create(email=email, defaults={'full_name': name, 'phone': phone, 'pay_rate': rate})
            teachers.append(teacher)

        student_names = [
            'Priya Sharma', 'Rahul Verma', 'Anisha Patel', 'Sanjay Joshi', 'Meera Thapa',
            'Kiran Bhatta', 'Nikita Rai', 'Bishnu Sharma', 'Asha Gurung', 'Ramesh KC',
            'Kabir Shrestha', 'Mina Adhikari', 'Suman Karki', 'Isha Basnet', 'Dev Rana',
        ]
        today = timezone.localdate()
        packages = list(Package.objects.filter(is_active=True))
        for index, name in enumerate(student_names):
            student, _ = Student.objects.get_or_create(full_name=name, defaults={'phone': f'+9779800{index:06d}', 'email': f'student{index}@dance.example'})
            package = packages[index % len(packages)]
            existing_enrollment = Enrollment.objects.filter(student=student).first()
            if existing_enrollment:
                if not existing_enrollment.time_slot:
                    existing_enrollment.time_slot = package.time_slots.order_by('start_time').first()
                    existing_enrollment.save(update_fields=['time_slot', 'updated_at'])
                continue
            if index % 3 == 0:
                entry = today - relativedelta(days=14)
                exit_date = today + relativedelta(days=7)
                active_slot = True
            elif index % 3 == 1:
                entry = today + relativedelta(days=5)
                exit_date = entry + relativedelta(months=1)
                active_slot = False
            else:
                entry = today - relativedelta(months=2)
                exit_date = today - relativedelta(days=2)
                active_slot = False
            paid = package.price if index % 3 == 0 else package.price / 2
            enrollment = Enrollment.objects.create(
                student=student, package=package,
                teacher=teachers[index % len(teachers)], entry_date=entry, exit_date=exit_date,
                time_slot=package.time_slots.order_by('start_time').first(),
                total_fee=package.price, amount_paid=paid,
                payment_status='PAID' if paid == package.price else 'PARTIAL', is_active=active_slot,
            )
            Invoice.objects.get_or_create(enrollment=enrollment, defaults={'invoice_number': Invoice.generate_number()})
            if paid:
                Payment.objects.get_or_create(enrollment=enrollment, amount=paid, defaults={'payment_method': 'CASH', 'paid_on': today})

        self.stdout.write(self.style.SUCCESS('Demo data seeding complete!'))
