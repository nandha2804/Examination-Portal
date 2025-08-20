from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from django.db.models import Q
from django.core.mail import send_mail
from django.contrib.auth.models import User
from student import models as SMODEL
from student import forms as SFORM
from django.contrib.auth.models import User
from teacher import models as TMODEL
from teacher import forms as TFORM
from django.contrib import messages
import random

def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'student/studentclick.html')

def teacherclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'teacher/teacherclick.html')

def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')  
    return render(request,'exam/index.html')

def contactus_view(request):
    if request.method == 'POST':
        message = request.POST['message']
        if request.user.is_authenticated:
            name = request.user.first_name
            email = request.user.email
            subject = "You have a new message from " + name
            message = "Name: " + name + "\nEmail: " + email + "\n\nMessage: " + message
            recipient_list = ['admin@example.com']
            try:
                send_mail(subject, message, email, recipient_list)
                return render(request, 'exam/contactussuccess.html')
            except:
                messages.error(request, "Failed to send message. Please try again later.")
        else:
            messages.error(request, "Please login first to contact us.")
    return render(request, 'exam/contactus.html')

def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

def afterlogin_view(request):
    if is_student(request.user):      
        return redirect('student/student-dashboard')
                
    elif is_teacher(request.user):
        accountapproval=TMODEL.Teacher.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('teacher/teacher-dashboard')
        else:
            return render(request,'teacher/teacher_wait_for_approval.html')
    else:
        return redirect('admin-dashboard')

def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')

@login_required(login_url='adminlogin')
def admin_teacher_view(request):
    return render(request,'exam/admin_teacher.html')

@login_required(login_url='adminlogin')
def admin_view_teacher_view(request):
    teachers= TMODEL.Teacher.objects.all().filter(status=True)
    return render(request,'exam/admin_view_teacher.html',{'teachers':teachers})

@login_required(login_url='adminlogin')
def update_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=TMODEL.User.objects.get(id=teacher.user_id)
    form1=TFORM.TeacherUserForm(instance=user)
    form2=TFORM.TeacherForm(instance=teacher)
    mydict={'form1':form1,'form2':form2}
    if request.method=='POST':
        form1=TFORM.TeacherUserForm(request.POST,instance=user)
        form2=TFORM.TeacherForm(request.POST,instance=teacher)
        if form1.is_valid() and form2.is_valid():
            user=form1.save()
            user.set_password(user.password)
            user.save()
            f2=form2.save(commit=False)
            f2.status=True
            f2.save()
            return redirect('admin-view-teacher')
    return render(request,'exam/update_teacher.html',context=mydict)

@login_required(login_url='adminlogin')
def delete_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return redirect('admin-view-teacher')

@login_required(login_url='adminlogin')
def admin_view_pending_teacher_view(request):
    teachers= TMODEL.Teacher.objects.all().filter(status=False)
    return render(request,'exam/admin_view_pending_teacher.html',{'teachers':teachers})

@login_required(login_url='adminlogin')
def approve_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    teacher.status=True
    teacher.save()
    return redirect('admin-view-pending-teacher')

@login_required(login_url='adminlogin')
def reject_teacher_view(request,pk):
    teacher=TMODEL.Teacher.objects.get(id=pk)
    user=User.objects.get(id=teacher.user_id)
    user.delete()
    teacher.delete()
    return redirect('admin-view-pending-teacher')

@login_required(login_url='adminlogin')
def admin_view_teacher_salary_view(request):
    teachers= TMODEL.Teacher.objects.all()
    return render(request,'exam/admin_view_teacher_salary.html',{'teachers':teachers})

@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    dict={
        'total_student':SMODEL.Student.objects.all().count(),
        'total_teacher':TMODEL.Teacher.objects.all().count(),
        'total_course':models.Course.objects.all().count(),
        'total_question':models.Question.objects.all().count(),
    }
    return render(request,'exam/admin_dashboard.html',context=dict)

@login_required(login_url='adminlogin')
def admin_seating_allocation_view(request):
    if request.method == 'POST':
        form = forms.BulkSeatingAllocationForm(request.POST)
        if form.is_valid():
            exam = form.cleaned_data['exam']
            room_count = form.cleaned_data['room_count']
            seats_per_room = form.cleaned_data['seats_per_room']
            
            # Get all students enrolled in the course
            students = SMODEL.Student.objects.filter(course=exam.course)
            
            # Delete existing allocations for this exam
            models.SeatingAllocation.objects.filter(exam=exam).delete()
            
            # Allocate seats
            current_room = 1
            current_seat = 1
            
            for student in students:
                # Create new allocation
                allocation = models.SeatingAllocation(
                    student=student,
                    exam=exam,
                    room_number=str(current_room),
                    seat_number=str(current_seat)
                )
                allocation.save()
                
                # Update room and seat numbers
                current_seat += 1
                if current_seat > seats_per_room:
                    current_seat = 1
                    current_room += 1
                    if current_room > room_count:
                        messages.warning(request, 'Not enough rooms for all students!')
                        break
            
            messages.success(request, 'Seating allocation completed successfully!')
            return redirect('admin-view-seating')
    else:
        form = forms.BulkSeatingAllocationForm()
    return render(request, 'exam/admin_seating_allocation.html', {'form': form})

@login_required(login_url='adminlogin')
def admin_view_seating_view(request):
    allocations = models.SeatingAllocation.objects.all().order_by('exam', 'room_number', 'seat_number')
    exams = models.Exam.objects.all()
    return render(request, 'exam/admin_view_seating.html', {
        'allocations': allocations,
        'exams': exams
    })

@login_required(login_url='adminlogin')
def edit_seating_allocation_view(request):
    if request.method == 'POST':
        allocation_id = request.POST.get('allocation_id')
        room_number = request.POST.get('room_number')
        seat_number = request.POST.get('seat_number')
        
        try:
            allocation = models.SeatingAllocation.objects.get(id=allocation_id)
            allocation.room_number = room_number
            allocation.seat_number = seat_number
            allocation.save()
            messages.success(request, 'Allocation updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating allocation: {str(e)}')
        
    return redirect('admin-view-seating')

@login_required(login_url='adminlogin')
def delete_seating_allocation_view(request):
    if request.method == 'POST':
        allocation_id = request.POST.get('allocation_id')
        try:
            allocation = models.SeatingAllocation.objects.get(id=allocation_id)
            allocation.delete()
            messages.success(request, 'Allocation deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting allocation: {str(e)}')
    
    return redirect('admin-view-seating')

@login_required(login_url='studentlogin')
def student_view_hall_ticket_view(request):
    student = SMODEL.Student.objects.get(user_id=request.user.id)
    allocation = models.SeatingAllocation.objects.filter(student=student).first()
    return render(request, 'student/view_hall_ticket.html', {'allocation': allocation})

@login_required(login_url='adminlogin')
def admin_student_view(request):
    return render(request,'exam/admin_student.html')

@login_required(login_url='adminlogin')
def admin_view_student_view(request):
    students = SMODEL.Student.objects.all()
    return render(request,'exam/admin_view_student.html',{'students':students})

@login_required(login_url='adminlogin')
def admin_view_student_marks_view(request):
    students= SMODEL.Student.objects.all()
    return render(request,'exam/admin_view_student_marks.html',{'students':students})

@login_required(login_url='adminlogin')
def admin_view_marks_view(request,pk):
    courses = models.Course.objects.all()
    response = render(request,'exam/admin_view_marks.html',{'courses':courses})
    return response

@login_required(login_url='adminlogin')
def admin_check_marks_view(request,pk):
    course = models.Course.objects.get(id=pk)
    student = SMODEL.Student.objects.get(id=pk)
    results= models.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request,'exam/admin_check_marks.html',{'results':results})

@login_required(login_url='adminlogin')
def update_student_view(request,pk):
    student=SMODEL.Student.objects.get(id=pk)
    user=SMODEL.User.objects.get(id=student.user_id)
    form1=SFORM.StudentUserForm(instance=user)
    form2=SFORM.StudentForm(instance=student)
    mydict={'form1':form1,'form2':form2}
    if request.method=='POST':
        form1=SFORM.StudentUserForm(request.POST,instance=user)
        form2=SFORM.StudentForm(request.POST,instance=student)
        if form1.is_valid() and form2.is_valid():
            user=form1.save()
            user.set_password(user.password)
            user.save()
            f2=form2.save(commit=False)
            f2.save()
            return redirect('admin-view-student')
    return render(request,'exam/update_student.html',context=mydict)

@login_required(login_url='adminlogin')
def delete_student_view(request,pk):
    student=SMODEL.Student.objects.get(id=pk)
    user=User.objects.get(id=student.user_id)
    user.delete()
    student.delete()
    return redirect('admin-view-student')

@login_required(login_url='adminlogin')
def admin_course_view(request):
    return render(request,'exam/admin_course.html')

@login_required(login_url='adminlogin')
def admin_add_course_view(request):
    courseForm=forms.CourseForm()
    if request.method=='POST':
        courseForm=forms.CourseForm(request.POST)
        if courseForm.is_valid():        
            courseForm.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-course')
    return render(request,'exam/admin_add_course.html',{'courseForm':courseForm})

@login_required(login_url='adminlogin')
def admin_view_course_view(request):
    courses = models.Course.objects.all()
    return render(request,'exam/admin_view_course.html',{'courses':courses})

@login_required(login_url='adminlogin')
def delete_course_view(request,pk):
    course=models.Course.objects.get(id=pk)
    course.delete()
    return HttpResponseRedirect('/admin-view-course')

@login_required(login_url='adminlogin')
def admin_question_view(request):
    return render(request,'exam/admin_question.html')

@login_required(login_url='adminlogin')
def admin_add_question_view(request):
    questionForm=forms.QuestionForm()
    if request.method=='POST':
        questionForm=forms.QuestionForm(request.POST)
        if questionForm.is_valid():
            question=questionForm.save(commit=False)
            course=models.Course.objects.get(id=request.POST.get('courseID'))
            question.course=course
            question.save()       
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-question')
    return render(request,'exam/admin_add_question.html',{'questionForm':questionForm})

@login_required(login_url='adminlogin')
def admin_view_question_view(request):
    courses= models.Course.objects.all()
    return render(request,'exam/admin_view_question.html',{'courses':courses})

@login_required(login_url='adminlogin')
def view_question_view(request,pk):
    questions=models.Question.objects.all().filter(course_id=pk)
    return render(request,'exam/view_question.html',{'questions':questions})

@login_required(login_url='adminlogin')
def delete_question_view(request,pk):
    question=models.Question.objects.get(id=pk)
    question.delete()
    return HttpResponseRedirect('/admin-view-question')
