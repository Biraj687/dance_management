"""
Dance Style views - Phase 1 live CRUD with real database queries.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import DanceStyle
from .forms import DanceStyleForm
from django.core.paginator import Paginator


@login_required
def style_list(request):
    """List all dance styles including soft-deleted ones (via all_objects)."""
    # Use all_objects to show both active and inactive styles
    styles = DanceStyle.all_objects.select_related().all()
    query = request.GET.get('q', '').strip()
    if query:
        styles = styles.filter(name__icontains=query)
    page = Paginator(styles, 25).get_page(request.GET.get('page'))
    
    context = {
        'styles': page,
        'page_obj': page,
        'page_title': 'Dance Styles', 'query': query,
    }
    return render(request, 'styles/list.html', context)


@login_required
def style_create(request):
    """Create new dance style with form validation."""
    if request.method == 'POST':
        form = DanceStyleForm(request.POST)
        if form.is_valid():
            style = form.save()
            messages.success(request, f'Dance style "{style.name}" created successfully.')
            return redirect('styles:list')
    else:
        form = DanceStyleForm(initial={'color_tag': '#F3A232', 'is_active': True})
    
    context = {
        'form': form,
        'form_action': 'styles:create',
        'page_title': 'Add Dance Style',
    }
    return render(request, 'styles/form.html', context)


@login_required
def style_edit(request, pk):
    """Edit existing dance style."""
    style = get_object_or_404(DanceStyle.all_objects, pk=pk)
    
    if request.method == 'POST':
        form = DanceStyleForm(request.POST, instance=style)
        if form.is_valid():
            style = form.save()
            messages.success(request, f'Dance style "{style.name}" updated successfully.')
            return redirect('styles:list')
    else:
        form = DanceStyleForm(instance=style)
    
    context = {
        'form': form,
        'style': style,
        'form_action': 'styles:edit',
        'form_action_kwargs': {'pk': pk},
        'page_title': f'Edit Dance Style: {style.name}',
    }
    return render(request, 'styles/form.html', context)


@login_required
def style_delete(request, pk):
    """
    Soft-delete a dance style.
    Blocks deletion if style has active packages referencing it.
    """
    style = get_object_or_404(DanceStyle.all_objects, pk=pk)
    
    # Check if style has active packages
    active_packages_count = style.packages.filter(is_active=True).count()
    if active_packages_count > 0:
        messages.error(
            request,
            f'Cannot deactivate "{style.name}" — it has {active_packages_count} '
            f'active package(s). Deactivate or reassign those packages first.'
        )
        return redirect('styles:list')
    
    if request.method == 'POST':
        name = style.name
        style.soft_delete()
        messages.success(request, f'Dance style "{name}" deactivated successfully.')
        return redirect('styles:list')
    
    # GET request - show confirmation
    context = {
        'style': style,
        'page_title': f'Deactivate Dance Style: {style.name}',
    }
    return render(request, 'styles/confirm_delete.html', context)


@login_required
def style_restore(request, pk):
    """Restore a soft-deleted dance style."""
    style = get_object_or_404(DanceStyle.all_objects, pk=pk)
    
    if not style.is_active:
        style.restore()
        messages.success(request, f'Dance style "{style.name}" restored successfully.')
    else:
        messages.info(request, f'Dance style "{style.name}" is already active.')
    
    return redirect('styles:list')