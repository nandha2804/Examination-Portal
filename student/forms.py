from django import forms
from django.contrib.auth.models import User
from . import models
from exam import models as QMODEL

class StudentUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }

class StudentForm(forms.ModelForm):
    class Meta:
        model=models.Student
        fields=['course', 'address','mobile','profile_pic']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show courses that have a batch assigned
        self.fields['course'].queryset = QMODEL.Course.objects.exclude(batch_name__isnull=True).exclude(batch_name__exact='')
        self.fields['course'].required = True
