from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.core.cache import cache
from django.db.models import Sum, Prefetch
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from . import forms, models
from exam import models as QMODEL
from teacher import models as TMODEL

# Cache timeout in seconds (30 minutes)
CACHE_TIMEOUT = 1800


#for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'student/studentclick.html')

def student_signup_view(request):
    userForm=forms.StudentUserForm()
    studentForm=forms.StudentForm()
    mydict={'userForm':userForm,'studentForm':studentForm}
    if request.method=='POST':
        userForm=forms.StudentUserForm(request.POST)
        studentForm=forms.StudentForm(request.POST,request.FILES)
        if userForm.is_valid() and studentForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            student=studentForm.save(commit=False)
            student.user=user
            student.save()
            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)
        return HttpResponseRedirect('studentlogin')
    return render(request,'student/studentsignup.html',context=mydict)

def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_dashboard_view(request):
    cache_key = f'student_dashboard_{request.user.id}'
    dashboard_data = cache.get(cache_key)
    
    if not dashboard_data:
        try:
            # Get student with related course data in one query
            student = models.Student.objects.select_related('course', 'user').get(user_id=request.user.id)
            course = student.course
            
            # Get upcoming exams with prefetched seating allocations
            upcoming_exams = (QMODEL.Exam.objects
                .filter(course=course, exam_date__gte=timezone.now().date())
                .prefetch_related(
                    Prefetch('seatingallocation_set',
                            queryset=QMODEL.SeatingAllocation.objects.filter(student=student),
                            to_attr='student_seating')
                )
                .order_by('exam_date'))

            # Process exam data
            exam_data = []
            for exam in upcoming_exams:
                seating = exam.student_seating[0] if exam.student_seating else None
                exam_data.append({
                    'id': exam.id,
                    'name': exam.course.course_name,
                    'date': exam.exam_date,
                    'has_seating': bool(seating),
                    'seat_number': seating.seat_number if seating else None,
                    'room': seating.room if seating else None
                })

            # Get completed exams count using cached value
            completed_key = f'completed_exams_{student.id}'
            completed_exam_count = cache.get(completed_key)
            if completed_exam_count is None:
                completed_exam_count = QMODEL.Result.objects.filter(student=student).count()
                cache.set(completed_key, completed_exam_count, CACHE_TIMEOUT)

            dashboard_data = {
                'course': course,
                'upcoming_exams': exam_data,
                'upcoming_exam_count': len(exam_data),
                'completed_exam_count': completed_exam_count,
            }
            
            # Cache the dashboard data
            cache.set(cache_key, dashboard_data, CACHE_TIMEOUT)
        
        except ObjectDoesNotExist:
            return render(request, 'student/student_dashboard.html', {
                'error': 'Student profile not found. Please contact administrator.'
            })
    
    return render(request, 'student/student_dashboard.html', context=dashboard_data)

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_exam_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_exam.html',{'courses':courses})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def take_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    total_questions=QMODEL.Question.objects.all().filter(course=course).count()
    questions=QMODEL.Question.objects.all().filter(course=course)
    total_marks=0
    for q in questions:
        total_marks=total_marks + q.marks
    
    return render(request,'student/take_exam.html',{'course':course,'total_questions':total_questions,'total_marks':total_marks})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def start_exam_view(request, pk):
    try:
        # Get course with prefetched questions
        course = QMODEL.Course.objects.prefetch_related('question_set').get(id=pk)
        
        # Check if student is allowed to take the exam
        student = models.Student.objects.get(user_id=request.user.id)
        if student.course != course:
            return render(request, 'student/start_exam.html', {
                'error': 'You are not enrolled in this course'
            })

        # Check if exam is already completed
        if QMODEL.Result.objects.filter(student=student, exam=course).exists():
            return render(request, 'student/start_exam.html', {
                'error': 'You have already completed this exam'
            })
        
        # Get cached questions or fetch from DB
        cache_key = f'course_questions_{pk}'
        questions = cache.get(cache_key)
        if not questions:
            questions = list(course.question_set.all().order_by('?'))  # Randomize questions
            cache.set(cache_key, questions, CACHE_TIMEOUT)

        response = render(request, 'student/start_exam.html', {
            'course': course,
            'questions': questions,
            'total_questions': len(questions)
        })
        
        # Set secure cookie with expiration
        response.set_cookie(
            'course_id',
            course.id,
            max_age=7200,  # 2 hours
            secure=True,
            httponly=True
        )
        return response

    except ObjectDoesNotExist:
        return render(request, 'student/start_exam.html', {
            'error': 'Course not found'
        })


@login_required(login_url='studentlogin')
@user_passes_test(is_student)
@require_http_methods(["POST"])
def calculate_marks_view(request):
    try:
        course_id = request.COOKIES.get('course_id')
        if not course_id:
            return JsonResponse({'error': 'No active exam found'}, status=400)

        # Get cached questions or fetch from DB
        cache_key = f'course_questions_{course_id}'
        questions = cache.get(cache_key)
        if not questions:
            course = QMODEL.Course.objects.prefetch_related('question_set').get(id=course_id)
            questions = list(course.question_set.all())
            cache.set(cache_key, questions, CACHE_TIMEOUT)

        # Calculate marks efficiently
        total_marks = sum(
            q.marks for i, q in enumerate(questions)
            if request.COOKIES.get(str(i+1)) == q.answer
        )

        # Save result
        student = models.Student.objects.get(user_id=request.user.id)
        QMODEL.Result.objects.create(
            marks=total_marks,
            exam_id=course_id,
            student=student
        )

        # Clear question cache after exam completion
        cache.delete(cache_key)
        
        # Clear dashboard cache to update completed exam count
        cache.delete(f'student_dashboard_{request.user.id}')
        cache.delete(f'completed_exams_{student.id}')

        return JsonResponse({
            'success': True,
            'redirect_url': reverse('view-result')
        })

    except Exception as e:
        return JsonResponse({
            'error': 'An error occurred while calculating marks'
        }, status=500)



@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def view_result_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/view_result.html',{'courses':courses})
    

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def check_marks_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    student = models.Student.objects.get(user_id=request.user.id)
    results= QMODEL.Result.objects.all().filter(exam=course).filter(student=student)    
    questions=QMODEL.Question.objects.all().filter(course=course)
    total_marks=0
    for q in questions:
        total_marks=total_marks + q.marks
    
    return render(request,'student/check_marks.html',{'results':results, 'total_marks':total_marks})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_marks_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_marks.html',{'courses':courses})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def view_hall_ticket(request, exam_id):
    student = models.Student.objects.get(user_id=request.user.id)
    try:
        allocation = QMODEL.SeatingAllocation.objects.get(
            exam_id=exam_id,
            student=student
        )
        allocations = [allocation]  # Put in list to maintain template compatibility
    except QMODEL.SeatingAllocation.DoesNotExist:
        allocations = []
    
    return render(request, 'student/view_hall_ticket.html', {
        'allocations': allocations
    })
