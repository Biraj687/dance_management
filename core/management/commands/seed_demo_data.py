"""
Management command to seed demo data for development and testing.
"""
from django.core.management.base import BaseCommand
from styles.models import DanceStyle
from packages.models import Package, PackageTimeSlot
from teachers.models import Teacher
from students.models import Student, Enrollment
from billing.models import Invoice, Payment
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from core.audit import log_audit_change


class Command(BaseCommand):
    help = 'Seed demo dance styles and packages'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')
        
        # Seed Dance Styles
        styles_data = [
            {'name': 'Salsa', 'description': 'Energetic Latin dance style with Afro-Cuban roots, characterized by hip movements and spins.', 'color_tag': '#E91E63', 'is_active': True},
            {'name': 'Hip Hop', 'description': 'Urban street dance style including breaking, locking, popping, and freestyle.', 'color_tag': '#673AB7', 'is_active': True},
            {'name': 'Classical Ballet', 'description': 'Formalized dance technique with precise gestures and poses, originating in Italian Renaissance courts.', 'color_tag': '#F3A232', 'is_active': True},
            {'name': 'Contemporary', 'description': 'Expressive dance combining elements of modern, jazz, lyrical, and classical ballet.', 'color_tag': '#00BCD4', 'is_active': True},
            {'name': 'Kathak', 'description': 'Classical Indian dance form with intricate footwork, spins, and expressive storytelling.', 'color_tag': '#FF5722', 'is_active': True},
            {'name': 'Bachata', 'description': 'Romantic Dominican dance with close partner connection and sensual body movements.', 'color_tag': '#8BC34A', 'is_active': True},
            {'name': 'Tango', 'description': 'Passionate Argentine partner dance with dramatic pauses and sharp movements.', 'color_tag': '#9C27B0', 'is_active': True},
        ]
        
        created_styles = []
        for style_data in styles_data:
            style, created = DanceStyle.all_objects.get_or_create(name=style_data['name'], defaults=style_data)
            if created:
                self.stdout.write(f'  Created style: {style.name}')
            else:
                if not style.is_active:
                    style.is_active = True
                    style.deleted_at = None
                    style.description = style_data['description']
                    style.color_tag = style_data['color_tag']
                    style.save(update_fields=['is_active', 'deleted_at', 'description', 'color_tag'])
                    self.stdout.write(f'  Restored style: {style.name}')
                else:
                    self.stdout.write(f'  Style exists: {style.name}')
            created_styles.append(style)
        # Seed Packages for each style
        packages_data = [
            {'style_name': 'Salsa', 'name': 'Salsa Beginner', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 12000, 'description': 'Basic Salsa steps and turns for beginners'},
            {'style_name': 'Salsa', 'name': 'Salsa Intermediate', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 15000, 'description': 'Intermediate patterns and styling'},
            {'style_name': 'Salsa', 'name': 'Salsa Advanced', 'duration_value': 3, 'duration_unit': 'MONTH', 'price': 40000, 'description': 'Advanced techniques and performance prep'},
            {'style_name': 'Hip Hop', 'name': 'Hip Hop Foundations', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 10000, 'description': 'Basic grooves, isolations, and freestyle'},
            {'style_name': 'Hip Hop', 'name': 'Hip Hop Choreography', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 13000, 'description': 'Learn trending choreographies'},
            {'style_name': 'Hip Hop', 'name': 'Hip Hop Intensive', 'duration_value': 2, 'duration_unit': 'MONTH', 'price': 22000, 'description': 'Comprehensive street dance training'},
            {'style_name': 'Classical Ballet', 'name': 'Ballet Basics', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 14000, 'description': 'Fundamental positions and barre work'},
            {'style_name': 'Classical Ballet', 'name': 'Ballet Intermediate', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 17000, 'description': 'Center work and pointe preparation'},
            {'style_name': 'Classical Ballet', 'name': 'Ballet Advanced', 'duration_value': 3, 'duration_unit': 'MONTH', 'price': 45000, 'description': 'Advanced repertoire and variations'},
            {'style_name': 'Contemporary', 'name': 'Contemporary Fundamentals', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 12000, 'description': 'Floor work, release technique, improvisation'},
            {'style_name': 'Contemporary', 'name': 'Contemporary Flow', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 14000, 'description': 'Choreography and emotional expression'},
            {'style_name': 'Kathak', 'name': 'Kathak Beginner', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 11000, 'description': 'Tatkar, chakkars, and basic bols'},
            {'style_name': 'Kathak', 'name': 'Kathak Intermediate', 'duration_value': 2, 'duration_unit': 'MONTH', 'price': 20000, 'description': 'Complex compositions and abhinaya'},
            {'style_name': 'Bachata', 'name': 'Bachata Beginner', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 10000, 'description': 'Basic steps and partner connection'},
            {'style_name': 'Bachata', 'name': 'Bachata Sensual', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 13000, 'description': 'Body waves, dips, and styling'},
            {'style_name': 'Tango', 'name': 'Tango Fundamentals', 'duration_value': 1, 'duration_unit': 'MONTH', 'price': 15000, 'description': 'Walk, embrace, and basic figures'},
            {'style_name': 'Tango', 'name': 'Tango Milonga', 'duration_value': 2, 'duration_unit': 'MONTH', 'price': 25000, 'description': 'Social dance preparation and milonga etiquette'},
        ]
        
        for pkg_data in packages_data:
            style = next((s for s in created_styles if s.name == pkg_data['style_name']), None)
            if not style:
                self.stdout.write(self.style.WARNING(f'  Style not found: {pkg_data["style_name"]}'))
                continue
            
            package, created = Package.all_objects.get_or_create(
                name=pkg_data['name'],
                dance_style=style,
                defaults={
                    'duration_value': pkg_data['duration_value'],
                    'duration_unit': pkg_data['duration_unit'],
                    'price': pkg_data['price'],
                    'description': pkg_data['description'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'  Created package: {package.name} ({style.name})')
            elif not package.is_active:
                package.is_active = True
                package.deleted_at = None
                package.duration_value = pkg_data['duration_value']
                package.duration_unit = pkg_data['duration_unit']
                package.price = pkg_data['price']
                package.description = pkg_data['description']
                package.save(update_fields=['is_active', 'deleted_at', 'duration_value', 'duration_unit', 'price', 'description'])
                self.stdout.write(f'  Restored package: {package.name} ({style.name})')
            else:
                self.stdout.write(f'  Package exists: {package.name} ({style.name})')
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
        for index, style in enumerate(created_styles):
            teachers[index % len(teachers)].assigned_styles.add(style)

        student_names = [
            'Priya Sharma', 'Rahul Verma', 'Anisha Patel', 'Sanjay Joshi', 'Meera Thapa',
            'Kiran Bhatta', 'Nikita Rai', 'Bishnu Sharma', 'Asha Gurung', 'Ramesh KC',
            'Kabir Shrestha', 'Mina Adhikari', 'Suman Karki', 'Isha Basnet', 'Dev Rana',
        ]
        today = timezone.localdate()
        packages = list(Package.objects.filter(is_active=True).select_related('dance_style'))
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
                student=student, package=package, dance_style_snapshot=package.dance_style,
                teacher=teachers[index % len(teachers)], entry_date=entry, exit_date=exit_date,
                time_slot=package.time_slots.order_by('start_time').first(),
                total_fee=package.price, amount_paid=paid,
                payment_status='PAID' if paid == package.price else 'PARTIAL', is_active=active_slot,
            )
            Invoice.objects.get_or_create(enrollment=enrollment, defaults={'invoice_number': Invoice.generate_number()})
            if paid:
                Payment.objects.get_or_create(enrollment=enrollment, amount=paid, defaults={'payment_method': 'CASH', 'paid_on': today})
        
        self.stdout.write(self.style.SUCCESS('Demo data seeding complete!'))