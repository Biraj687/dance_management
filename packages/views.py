from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Count, Q, Prefetch

from .forms import PackageForm, PackageTimeSlotFormSet
from .models import Package, PackageTimeSlot


@login_required
def package_list(request):
    slots = PackageTimeSlot.objects.annotate(active_count=Count('enrollments', filter=Q(enrollments__is_active=True))).order_by('start_time')
    packages = Package.all_objects.select_related('dance_style').prefetch_related(Prefetch('time_slots', queryset=slots)).order_by('dance_style__name', 'name')
    query = request.GET.get('q', '').strip()
    if query:
        packages = packages.filter(name__icontains=query) | packages.filter(dance_style__name__icontains=query)
    packages = packages.distinct()
    page = Paginator(packages, 25).get_page(request.GET.get('page'))
    return render(request, 'packages/list.html', {'packages': page, 'page_obj': page, 'page_title': 'Packages', 'query': query})


@login_required
def package_create(request):
    form = PackageForm(request.POST or None)
    slot_formset = PackageTimeSlotFormSet(request.POST or None, prefix='times')
    if form.is_valid() and slot_formset.is_valid():
        package = form.save()
        slot_formset.instance = package
        slot_formset.save()
        messages.success(request, f'Package "{package.name}" created successfully.')
        return redirect('packages:list')
    return render(request, 'packages/form.html', {'form': form, 'slot_formset': slot_formset, 'form_action': 'packages:create', 'page_title': 'Add Package'})


@login_required
def package_edit(request, pk):
    package = get_object_or_404(Package.all_objects, pk=pk)
    form = PackageForm(request.POST or None, instance=package)
    slot_formset = PackageTimeSlotFormSet(request.POST or None, instance=package, prefix='times')
    if form.is_valid() and slot_formset.is_valid():
        form.save()
        slot_formset.save()
        messages.success(request, f'Package "{package.name}" updated successfully.')
        return redirect('packages:list')
    return render(request, 'packages/form.html', {'form': form, 'slot_formset': slot_formset, 'package': package, 'form_action': 'packages:edit', 'form_action_kwargs': {'pk': pk}, 'page_title': 'Edit Package'})


@login_required
def package_delete(request, pk):
    package = get_object_or_404(Package.all_objects, pk=pk)
    if request.method == 'POST':
        package.soft_delete()
        messages.success(request, f'Package "{package.name}" deactivated.')
    return redirect('packages:list')
