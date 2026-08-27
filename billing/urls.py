from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.invoice_list, name='list'),
    path('<int:pk>/', views.invoice_detail, name='detail'),
    path('<int:pk>/download/', views.invoice_download, name='download'),
    path('<int:pk>/payment/', views.payment_create, name='payment'),
    path('export/students.csv', views.export_students_csv, name='export_students_csv'),
    path('export/teachers.csv', views.export_teachers_csv, name='export_teachers_csv'),
    path('export/ledger.csv', views.export_ledger_csv, name='export_ledger_csv'),
    path('export/students.pdf', views.export_students_pdf, name='export_students_pdf'),
    path('export/teachers.pdf', views.export_teachers_pdf, name='export_teachers_pdf'),
    path('export/ledger.pdf', views.export_ledger_pdf, name='export_ledger_pdf'),
]