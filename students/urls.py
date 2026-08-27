from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list, name='list'),
    path('create/', views.student_create, name='create'),
    path('enroll/', views.student_enroll, name='enroll'),
    path('<int:pk>/enroll/', views.enroll_for_student, name='enroll_for_student'),
    path('<int:pk>/renew/', views.student_renew, name='renew'),
    path('<int:pk>/', views.student_detail, name='detail'),
    path('<int:pk>/edit/', views.student_edit, name='edit'),
]