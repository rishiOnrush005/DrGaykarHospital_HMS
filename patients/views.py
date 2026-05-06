import csv
import io
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Patient
from .forms import PatientForm
from django.db.models import Q

CSV_REQUIRED_COLUMNS = ['Name', 'Age', 'Gender', 'Phone', 'Village', 'Blood Group']
CSV_DANGEROUS_PREFIXES = ('=', '+', '-', '@', '\t', '\r')
MAX_CSV_UPLOAD_SIZE = 5 * 1024 * 1024
MAX_CSV_IMPORT_ROWS = 5000


def _csv_safe(value):
    text = '' if value is None else str(value)
    return f"'{text}" if text.startswith(CSV_DANGEROUS_PREFIXES) else text


@login_required
def export_patients_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="patients_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Patient ID', 'Name', 'Age', 'Gender', 'Phone', 'Village', 'Blood Group'])
    
    patients = Patient.objects.all().iterator()
    for p in patients:
        writer.writerow([
            _csv_safe(p.patient_id),
            _csv_safe(p.name),
            _csv_safe(p.age),
            _csv_safe(p.gender),
            _csv_safe(p.phone),
            _csv_safe(p.village),
            _csv_safe(p.blood_group),
        ])
    
    return response

@login_required
def import_patients_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, "Please choose a CSV file to import.")
            return render(request, 'patients/import.html')

        if not csv_file.name.lower().endswith('.csv'):
            messages.error(request, "Only .csv files can be imported.")
            return render(request, 'patients/import.html')

        if csv_file.size > MAX_CSV_UPLOAD_SIZE:
            messages.error(request, "CSV file is too large.")
            return render(request, 'patients/import.html')

        try:
            decoded_file = csv_file.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            messages.error(request, "CSV file must be UTF-8 encoded.")
            return render(request, 'patients/import.html')

        reader = csv.DictReader(io.StringIO(decoded_file))
        missing_columns = [column for column in CSV_REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing_columns:
            messages.error(request, f"CSV is missing required columns: {', '.join(missing_columns)}")
            return render(request, 'patients/import.html')

        count = 0
        row_number = 1
        try:
            with transaction.atomic():
                for row_number, row in enumerate(reader, start=2):
                    if count >= MAX_CSV_IMPORT_ROWS:
                        raise ValidationError(f"CSV import is limited to {MAX_CSV_IMPORT_ROWS} rows.")

                    cleaned = {column: (row.get(column) or '').strip() for column in CSV_REQUIRED_COLUMNS}
                    age = int(cleaned['Age'])
                    if cleaned['Gender'] not in {'M', 'F', 'O'}:
                        raise ValidationError("Gender must be M, F, or O.")

                    Patient.objects.get_or_create(
                        name=cleaned['Name'],
                        age=age,
                        gender=cleaned['Gender'],
                        phone=cleaned['Phone'],
                        village=cleaned['Village'],
                        blood_group=cleaned['Blood Group']
                    )
                    count += 1
        except (ValueError, ValidationError) as e:
            message = ' '.join(e.messages) if hasattr(e, 'messages') else str(e)
            messages.error(request, f"Import failed at row {row_number}: {message}")
            return render(request, 'patients/import.html')

        messages.success(request, f"Successfully imported {count} patients.")
        return redirect('patient_list')
    
    return render(request, 'patients/import.html')

# (Existing views: list, register, detail follow...)
@login_required
def patient_list(request):
    query = request.GET.get('q')
    if query:
        patients = Patient.objects.filter(
            Q(patient_id__icontains=query) |
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(village__icontains=query)
        )
    else:
        patients = Patient.objects.all().order_by('-registered_on')
    return render(request, 'patients/patient_list.html', {'patients': patients, 'query': query})

@login_required
def patient_register(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            if request.user.role == 'doctor':
                return redirect('patient_detail', uuid=patient.uuid)
            else:
                return redirect('record_visit', patient_uuid=patient.uuid)
    else:
        form = PatientForm()
    return render(request, 'patients/patient_form.html', {'form': form})

@login_required
def patient_detail(request, uuid):
    if request.user.role != 'doctor':
        messages.error(request, "Access denied. Only doctors can view patient medical records.")
        return redirect('dashboard')
    
    patient = get_object_or_404(Patient.objects.prefetch_related('visits__attended_by'), uuid=uuid)
    visits = patient.visits.all().order_by('-visited_on')
    return render(request, 'patients/patient_detail.html', {'patient': patient, 'visits': visits})
