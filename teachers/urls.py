from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list, name='list'),
    path('<int:pk>/', views.teacher_detail, name='detail'),
    path('create/', views.teacher_create, name='create'),
    path('<int:pk>/edit/', views.teacher_edit, name='edit'),
    path('<int:pk>/deactivate/', views.teacher_deactivate, name='deactivate'),
    path('<int:pk>/schedule/', views.teacher_schedule, name='schedule'),
]