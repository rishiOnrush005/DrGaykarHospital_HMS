from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import CustomUser
from .forms import StaffCreationForm

@login_required
def staff_list(request):
    if request.user.role != 'doctor':
        messages.error(request, "Access denied. Only doctors can manage staff.")
        return redirect('dashboard')
    
    staff_members = CustomUser.objects.filter(role='staff')
    return render(request, 'accounts/staff_list.html', {'staff_members': staff_members})

@login_required
def create_staff(request):
    if request.user.role != 'doctor':
        messages.error(request, "Access denied. Only doctors can manage staff.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New staff member created successfully.")
            return redirect('staff_list')
    else:
        form = StaffCreationForm()
    
    return render(request, 'accounts/staff_form.html', {'form': form})

@login_required
@require_POST
def delete_staff(request, pk):
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    staff = get_object_or_404(CustomUser, pk=pk, role='staff')
    staff.delete()
    messages.success(request, "Staff member removed.")
    return redirect('staff_list')
