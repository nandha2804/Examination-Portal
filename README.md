# Online-Examination-System
Online Examination System using Python and Django.

# Overview
This project is a fully functional Online Examination System developed using the Python Django web framework. It is designed for educational institutions, allowing students to take exams online, while teachers and administrators manage courses, questions, and student records efficiently. This system is ideal for IT students in their first or second year, and it simulates a real-life examination environment with an intuitive user interface.

# Key Features
## Student Panel
* Register and login to access exams
* View available courses and exam sets
* Attend multiple-choice questions (MCQ) based exams
* View marks and number of attempts post-submission

## Teacher Panel
* Account approval required from admin for activation
* Manage courses by adding questions, options, and correct answers
* View total number of students enrolled

## Admin Panel
* Full control of the system, including user management
* Approve or decline teacher accounts and set teacher salaries
* Manage courses and questions sets similar to the teacher role
* View student marks and exam attempts

## Technologies Used
* Backend: Python, Django Web Framework
* Frontend: HTML, CSS, Bootstrap
* Database: SQLite

## How to Run the Project
* Clone the repository.
* Set up a virtual environment.
* Install the required dependencies using pip install -r requirements.txt.
* Apply migrations using python manage.py migrate.
* Run the server with python manage.py runserver.
