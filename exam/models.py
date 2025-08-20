from django.db import models

from student.models import Student
class Course(models.Model):
    course_name = models.CharField(max_length=50)
    question_number = models.PositiveIntegerField()
    total_marks = models.PositiveIntegerField()
    assigned_teacher = models.ForeignKey('teacher.Teacher', on_delete=models.SET_NULL, null=True, blank=True)
    batch_name = models.CharField(max_length=50, null=True, blank=True)
    batch_year = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.course_name} - {self.batch_name} ({self.batch_year})"

    class Meta:
    option2=models.CharField(max_length=200)
    option3=models.CharField(max_length=200)
    option4=models.CharField(max_length=200)
    cat=(('Option1','Option1'),('Option2','Option2'),('Option3','Option3'),('Option4','Option4'))
    answer=models.CharField(max_length=200,choices=cat)

class Result(models.Model):
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    exam = models.ForeignKey(Course,on_delete=models.CASCADE)
    marks = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now=True)

class SeatingAllocation(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Course, on_delete=models.CASCADE)
    room_number = models.CharField(max_length=10)
    seat_number = models.CharField(max_length=10)
    exam_date = models.DateTimeField()
    hall_ticket_number = models.CharField(max_length=20, unique=True)
    
    def save(self, *args, **kwargs):
        if not self.hall_ticket_number:
            # Generate hall ticket number format: EXAM<course_id>STU<student_id>R<room>S<seat>
            self.hall_ticket_number = f"EXAM{self.exam.id}STU{self.student.id}R{self.room_number}S{self.seat_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.get_name} - {self.exam.course_name} - Room {self.room_number}"
