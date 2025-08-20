from django import forms
from django.forms import ModelForm
from .models import Course, Question, SeatingAllocation
from student.models import Student

class CourseForm(forms.ModelForm):
    class Meta:
        model=Course
        fields=['course_name','question_number','total_marks', 'batch_name', 'batch_year']

class QuestionForm(forms.ModelForm):
    class Meta:
        model=Question
        fields=['marks','question','option1','option2','option3','option4','answer']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3, 'cols': 50})
        }

class SeatingAllocationForm(forms.ModelForm):
    class Meta:
        model = SeatingAllocation
        fields = ['student', 'exam', 'room_number', 'seat_number']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'exam': forms.Select(attrs={'class': 'form-control'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'seat_number': forms.TextInput(attrs={'class': 'form-control'})
        }

class BulkSeatingAllocationForm(forms.Form):
    exam = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    room_count = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    seats_per_room = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Exam
        self.fields['exam'].queryset = Exam.objects.all()
