from django.shortcuts import render, redirect, reverse
from . import forms, models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from exam import models as QMODEL
from student import models as SMODEL
from exam import forms as QFORM
from teacher.models import Teacher

def teacherclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'teacher/teacherclick.html')

def teacher_signup_view(request):
    userForm = forms.TeacherUserForm()
    teacherForm = forms.TeacherForm()
    mydict = {'userForm': userForm, 'teacherForm': teacherForm}
    if request.method == 'POST':
        userForm = forms.TeacherUserForm(request.POST)
        teacherForm = forms.TeacherForm(request.POST, request.FILES)
        if userForm.is_valid() and teacherForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            teacher = teacherForm.save(commit=False)
            teacher.user = user
            teacher.save()
            my_teacher_group = Group.objects.get_or_create(name='TEACHER')
            my_teacher_group[0].user_set.add(user)
        return HttpResponseRedirect('teacherlogin')
    return render(request, 'teacher/teachersignup.html', context=mydict)

def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_dashboard_view(request):
    teacher = models.Teacher.objects.get(user_id=request.user.id)
    dict = {
        'total_course': QMODEL.Course.objects.filter(assigned_teacher=teacher).count(),
        'total_question': QMODEL.Question.objects.filter(course__assigned_teacher=teacher).count(),
        'total_exam': QMODEL.Exam.objects.filter(created_by=teacher).count(),
        'total_student': SMODEL.Student.objects.filter(course__assigned_teacher=teacher).count()
    }
    return render(request, 'teacher/teacher_dashboard.html', context=dict)

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_exam_view(request):
    teacher = models.Teacher.objects.get(user_id=request.user.id)
    exams = QMODEL.Exam.objects.filter(created_by=teacher)
    return render(request, 'teacher/teacher_exam.html', {'exams': exams})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def create_exam_view(request):
    teacher = models.Teacher.objects.get(user_id=request.user.id)
    examForm = QFORM.ExamForm(teacher=teacher)
    
    if request.method == 'POST':
        examForm = QFORM.ExamForm(teacher=teacher, data=request.POST)
        if examForm.is_valid():
            exam = examForm.save(commit=False)
            exam.created_by = teacher
            exam.save()
            return HttpResponseRedirect('/teacher/teacher-exam')
    
    return render(request, 'teacher/create_exam.html', {'examForm': examForm})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def delete_exam_view(request, pk):
    exam = QMODEL.Exam.objects.get(id=pk)
    if exam.created_by.user_id == request.user.id:
        exam.delete()
    return HttpResponseRedirect('/teacher/teacher-exam')

@login_required(login_url='teacherlogin')
def teacher_question_view(request):
    return render(request, 'teacher/teacher_question.html')

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_add_question_view(request):
    teacher = models.Teacher.objects.get(user_id=request.user.id)
    questionForm = QFORM.QuestionForm()
    if request.method == 'POST':
        questionForm = QFORM.QuestionForm(request.POST)
        if questionForm.is_valid():
            question = questionForm.save(commit=False)
            course = QMODEL.Course.objects.get(id=request.POST.get('courseID'))
            if course.assigned_teacher == teacher:
                question.course = course
                question.save()
        return HttpResponseRedirect('/teacher/teacher-view-question')
    return render(request, 'teacher/teacher_add_question.html', {'questionForm': questionForm})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_question_view(request):
    teacher = models.Teacher.objects.get(user_id=request.user.id)
    courses = QMODEL.Course.objects.filter(assigned_teacher=teacher)
    return render(request, 'teacher/teacher_view_question.html', {'courses': courses})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def see_question_view(request, pk):
    teacher = models.Teacher.objects.get(user_id=request.user.id)
    course = QMODEL.Course.objects.get(id=pk)
    if course.assigned_teacher == teacher:
        questions = QMODEL.Question.objects.filter(course_id=pk)
        return render(request, 'teacher/see_question.html', {'questions': questions})
    return HttpResponseRedirect('/teacher/teacher-question')

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def remove_question_view(request, pk):
    teacher = models.Teacher.objects.get(user_id=request.user.id)
    question = QMODEL.Question.objects.get(id=pk)
    if question.course.assigned_teacher == teacher:
        question.delete()
    return HttpResponseRedirect('/teacher/teacher-view-question')
