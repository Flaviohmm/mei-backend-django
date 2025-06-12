from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('user/', views.get_user_details, name='get_user_details'),
    path('logout/', views.logout, name='logout'),
]
