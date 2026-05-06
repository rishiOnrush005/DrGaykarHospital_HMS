from django import forms
from .models import Visit

class VisitVitalsForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['weight', 'bp', 'temp', 'sugar']
        widgets = {
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight (kg)'}),
            'bp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BP (120/80)'}),
            'temp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Temp (98.6 F)'}),
            'sugar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sugar (mg/dL)'}),
        }

class VisitClinicalForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['symptoms', 'diagnosis', 'prescription_text', 'prescription_photo', 'follow_up_date']
        widgets = {
            'symptoms': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'prescription_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prescription_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'follow_up_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
