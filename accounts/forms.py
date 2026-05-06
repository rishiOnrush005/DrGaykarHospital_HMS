from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser

class StaffCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'phone', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 9876543210'}),
        }

    def clean_password(self):
        password = self.cleaned_data['password']
        user = CustomUser(
            username=self.cleaned_data.get('username', ''),
            first_name=self.cleaned_data.get('first_name', ''),
            last_name=self.cleaned_data.get('last_name', ''),
            phone=self.cleaned_data.get('phone', ''),
        )
        validate_password(password, user)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = 'staff'
        if commit:
            user.save()
        return user
