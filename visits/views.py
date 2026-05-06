from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Visit
from patients.models import Patient
from .forms import VisitVitalsForm, VisitClinicalForm
from django.contrib import messages

@login_required
def record_visit(request, patient_uuid):
    # Staff/Receptionist records initial vitals and puts patient in queue
    patient = get_object_or_404(Patient, uuid=patient_uuid)
    if request.method == 'POST':
        form = VisitVitalsForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.patient = patient
            visit.status = 'pending'
            visit.save()
            messages.success(request, f"{patient.name} has been added to the queue.")
            return redirect('patient_detail', uuid=patient.uuid)
    else:
        form = VisitVitalsForm()
    return render(request, 'visits/visit_form.html', {
        'form': form, 
        'patient': patient,
        'title': 'Add to Queue'
    })

@login_required
def complete_visit(request, visit_uuid):
    # Doctor picks up patient from queue and records clinical details
    if request.user.role != 'doctor':
        messages.error(request, "Only doctors can record clinical information.")
        return redirect('dashboard')
        
    visit = get_object_or_404(Visit, uuid=visit_uuid)
    if request.method == 'POST':
        form = VisitClinicalForm(request.POST, request.FILES, instance=visit)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.status = 'completed'
            visit.attended_by = request.user
            visit.save()
            messages.success(request, f"Visit for {visit.patient.name} completed.")
            return redirect('dashboard')
    else:
        form = VisitClinicalForm(instance=visit)
    
    return render(request, 'visits/visit_form.html', {
        'form': form, 
        'patient': visit.patient,
        'visit': visit,
        'title': 'Clinical Examination'
    })
