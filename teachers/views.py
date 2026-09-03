from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TeacherForm
from .models import Teacher
from .availability_forms import TeacherAvailabilityForm


@login_required
def teacher_list(request):
    teachers = Teacher.all_objects.order_by('full_name')
    query = request.GET.get('q', '').strip()
    if query:
        teachers = teachers.filter(Q(full_name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query))
    sort = request.GET.get('sort', 'full_name')
    if sort in {'full_name', '-full_name', 'pay_rate', '-pay_rate'}:
        teachers = teachers.order_by(sort)
    elif sort in {'active_students', '-active_students'}:
        teachers = teachers.annotate(
            current_students=Count('enrollments', filter=Q(enrollments__is_active=True))
        ).order_by('-current_students' if sort == 'active_students' else 'current_students')
    page = Paginator(teachers, 25).get_page(request.GET.get('page'))
    return render(request, 'teachers/list.html', {'teachers': page, 'page_obj': page, 'page_title': 'Teachers', 'query': query, 'sort': sort})


@login_required
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher.objects.prefetch_related('enrollments__student'), pk=pk)
    return render(request, 'teachers/detail.html', {'teacher': teacher, 'page_title': teacher.full_name})


@login_required
def teacher_create(request):
    form = TeacherForm(request.POST or None)
    if form.is_valid():
        teacher = form.save()
        messages.success(request, f'Teacher "{teacher.full_name}" created successfully.')
        return redirect('teachers:list')
    return render(request, 'teachers/form.html', {'form': form, 'form_action': 'teachers:create', 'page_title': 'Add Teacher'})


@login_required
def teacher_edit(request, pk):
    teacher = get_object_or_404(Teacher.all_objects, pk=pk)
    form = TeacherForm(request.POST or None, instance=teacher)
    if form.is_valid():
        form.save()
        messages.success(request, f'Teacher "{teacher.full_name}" updated successfully.')
        return redirect('teachers:detail', pk=pk)
    return render(request, 'teachers/form.html', {'form': form, 'teacher': teacher, 'form_action': 'teachers:edit', 'form_action_kwargs': {'pk': pk}, 'page_title': 'Edit Teacher'})


@login_required
def teacher_deactivate(request, pk):
    teacher = get_object_or_404(Teacher.all_objects, pk=pk)
    if teacher.active_assigned_student_count:
        messages.error(request, f'Cannot deactivate this teacher until {teacher.active_assigned_student_count} active student assignment(s) are reassigned.')
    elif request.method == 'POST':
        teacher.soft_delete()
        messages.success(request, f'Teacher "{teacher.full_name}" deactivated.')
    return redirect('teachers:list')


@login_required
def teacher_schedule(request, pk):
    teacher = get_object_or_404(Teacher.objects.prefetch_related('availability_slots'), pk=pk)
    form = TeacherAvailabilityForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        slot = form.save(commit=False)
        slot.teacher = teacher
        slot.save()
        messages.success(request, 'Availability slot added.')
        return redirect('teachers:schedule', pk=pk)
    return render(request, 'teachers/schedule.html', {'teacher': teacher, 'slots': teacher.availability_slots.all(), 'form': form, 'page_title': f'{teacher.full_name} Schedule'})
