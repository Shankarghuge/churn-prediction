
from django.contrib import admin
from django.urls import path
from app import views
urlpatterns = [
    path('', views.index, name='index.html'),
    path('register', views.register, name='register'),
    path('log_in', views.log_in, name='log_in'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('upload_file', views.upload_file, name='upload_file'),
    path('download/', views.download_churn_customers, name='download_churn_customers'),
    path('log_out/',views.log_out, name='log_out'),
    path("send-email/", views.send_email, name="send_email"),
]


