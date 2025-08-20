from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.core.cache import cache
from django.db.models import Sum, Count, Prefetch
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from . import forms, models
from exam import models as QMODEL
from student import models as SMODEL
from exam import forms as QFORM
from teacher.models import Teacher

# Cache timeout in seconds (30 minutes)
CACHE_TIMEOUT = 1800

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
    cache_key = f'teacher_dashboard_{request.user.id}'
    dashboard_data = cache.get(cache_key)
    
    if not dashboard_data:
        try:
            # Get teacher with related data
            teacher = models.Teacher.objects.select_related('user').get(user_id=request.user.id)
            
            # Get courses with prefetched data
            courses = (QMODEL.Course.objects
                .filter(assigned_teacher=teacher)
                .prefetch_related(
                    Prefetch(
                        'student_set',
                        queryset=SMODEL.Student.objects.all(),
                        to_attr='enrolled_students'
                    ),
                    Prefetch(
                        'exam_set',
                        queryset=QMODEL.Exam.objects.filter(
                            exam_date__gte=timezone.now()
                        ).order_by('exam_date'),
                        to_attr='upcoming_exams'
                    )
                ))
            
            # Process course data
            course_data = []
            for course in courses:
                course_data.append({
                    'id': course.id,
                    'name': course.course_name,
                    'student_count': len(course.enrolled_students),
                    'next_exam': course.upcoming_exams[0] if course.upcoming_exams else None
                })

            # Get counts efficiently
            total_question = QMODEL.Question.objects.filter(
                course__assigned_teacher=teacher
            ).count()
            
            total_exam = QMODEL.Exam.objects.filter(
                created_by=teacher
            ).count()
            
            total_student = sum(len(course.enrolled_students) for course in courses)

            dashboard_data = {
                'total_course': len(courses),
                'total_question': total_question,
                'total_exam': total_exam,
                'total_student': total_student,
                'courses': course_data
            }
            
            # Cache the dashboard data
            cache.set(cache_key, dashboard_data, CACHE_TIMEOUT)
            
        except ObjectDoesNotExist:
            return render(request, 'teacher/teacher_dashboard.html', {
                'error': 'Teacher profile not found. Please contact administrator.'
            })
    
    return render(request, 'teacher/teacher_dashboard.html', context=dashboard_data)

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
    try:
        teacher = models.Teacher.objects.select_related('user').get(user_id=request.user.id)
        
        if request.method == 'POST':
            questionForm = QFORM.QuestionForm(request.POST)
            if questionForm.is_valid():
                course = get_object_or_404(QMODEL.Course, id=request.POST.get('courseID'))
                
                # Verify teacher owns this course
                if course.assigned_teacher != teacher:
                    raise PermissionDenied("You don't have permission to add questions to this course.")
                
                question = questionForm.save(commit=False)
                question.course = course
                question.save()
                
                # Clear related caches
                cache.delete(f'course_questions_{course.id}')
                cache.delete(f'teacher_dashboard_{request.user.id}')
                
                return JsonResponse({
                    'success': True,
                    'message': 'Question added successfully',
                    'redirect_url': reverse('teacher-view-question')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': questionForm.errors
                }, status=400)
                
        questionForm = QFORM.QuestionForm()
        return render(request, 'teacher/teacher_add_question.html', {
            'questionForm': questionForm,
            'teacher': teacher
        })
        
    except (ObjectDoesNotExist, PermissionDenied) as e:
        return JsonResponse({
            'error': str(e)
        }, status=403)
    except Exception as e:
        return JsonResponse({
            'error': 'An error occurred while processing your request'
        }, status=500)

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_question_view(request):
    teacher = models.Teacher.objects.get(user_id=request.user.id)
    courses = QMODEL.Course.objects.filter(assigned_teacher=teacher)
    return render(request, 'teacher/teacher_view_question.html', {'courses': courses})

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def see_question_view(request, pk):
    try:
        teacher = models.Teacher.objects.select_related('user').get(user_id=request.user.id)
        course = get_object_or_404(QMODEL.Course, id=pk)
        
        if course.assigned_teacher != teacher:
            raise PermissionDenied("You don't have permission to view these questions.")
        
        # Try to get cached questions
        cache_key = f'course_questions_{pk}'
        questions = cache.get(cache_key)
        
        if questions is None:
            questions = list(QMODEL.Question.objects
                .filter(course_id=pk)
                .select_related('course')
                .order_by('id'))
            cache.set(cache_key, questions, CACHE_TIMEOUT)
        
        return render(request, 'teacher/see_question.html', {
            'questions': questions,
            'course': course
        })
        
    except PermissionDenied as e:
        return render(request, 'teacher/see_question.html', {
            'error': str(e)
        }, status=403)
    except Exception:
        return render(request, 'teacher/see_question.html', {
            'error': 'An error occurred while retrieving questions'
        }, status=500)

@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def remove_question_view(request, pk):
    teacher = models.Teacher.objects.get(user_id=request.user.id)
    question = QMODEL.Question.objects.get(id=pk)
    if question.course.assigned_teacher == teacher:
        question.delete()
    return HttpResponseRedirect('/teacher/teacher-view-question')
