from django import forms
from django.contrib.auth.models import User
from . import models

class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))

class TeacherSalaryForm(forms.Form):
    salary=forms.IntegerField()

class CourseForm(forms.ModelForm):
    class Meta:
        model=models.Course
        fields=['course_name', 'batch_name', 'batch_year', 'assigned_teacher', 'question_number', 'total_marks']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show approved teachers
        from teacher.models import Teacher
        self.fields['assigned_teacher'].queryset = Teacher.objects.filter(status=True)

class ExamForm(forms.ModelForm):
    class Meta:
        model=models.Exam
        fields=['course', 'exam_name', 'exam_date', 'start_time', 'duration']
        widgets = {
            'exam_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, teacher=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            # Only show courses assigned to this teacher
            self.fields['course'].queryset = models.Course.objects.filter(assigned_teacher=teacher)

class QuestionForm(forms.ModelForm):
    
    #this will show dropdown __str__ method course model is shown on html so override it
    #to_field_name this will fetch corresponding value  user_id present in course model and return it
    courseID=forms.ModelChoiceField(queryset=models.Course.objects.all(),empty_label="Course Name", to_field_name="id")
    class Meta:
        model=models.Question
        fields=['marks','question','option1','option2','option3','option4','answer']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3, 'cols': 50})
        }
