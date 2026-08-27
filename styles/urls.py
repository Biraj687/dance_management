from django.urls import path
from . import views

app_name = 'styles'

urlpatterns = [
    path('', views.style_list, name='list'),
    path('create/', views.style_create, name='create'),
    path('<int:pk>/edit/', views.style_edit, name='edit'),
    path('<int:pk>/delete/', views.style_delete, name='delete'),
    path('<int:pk>/restore/', views.style_restore, name='restore'),
]