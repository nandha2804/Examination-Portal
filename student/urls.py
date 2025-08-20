from django.urls import path
from student import views as student_views
from django.contrib.auth.views import LoginView
from exam import views as exam_views

urlpatterns = [
path('studentclick', student_views.studentclick_view),
path('studentlogin', LoginView.as_view(template_name='student/studentlogin.html'),name='studentlogin'),
path('studentsignup', student_views.student_signup_view,name='studentsignup'),
path('student-dashboard', student_views.student_dashboard_view,name='student-dashboard'),
path('student-exam', student_views.student_exam_view,name='student-exam'),
path('take-exam/<int:pk>', student_views.take_exam_view,name='take-exam'),
path('start-exam/<int:pk>', student_views.start_exam_view,name='start-exam'),

path('calculate-marks', student_views.calculate_marks_view,name='calculate-marks'),
path('view-result', student_views.view_result_view,name='view-result'),
path('check-marks/<int:pk>', student_views.check_marks_view,name='check-marks'),
path('student-marks', student_views.student_marks_view,name='student-marks'),
path('view-hall-ticket', exam_views.student_view_hall_ticket_view, name='view-hall-ticket'),
]
