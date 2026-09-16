"""manage_project URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('dashboard.urls')),
    path('students/', include('students.urls')),
    path('teachers/', include('teachers.urls')),
    path('packages/', include('packages.urls')),
    path('billing/', include('billing.urls')),
    path('search/', include('search.urls')),
    path('', accounts_views.root_redirect, name='root'),
]

handler404 = 'dashboard.views.custom_404'
handler500 = 'dashboard.views.custom_500'