
from django.urls import path
from . import views


urlpatterns = [

    # Authentication

    path('login/', views.login_view, name='login'),

    path('register/', views.register_view, name='register'),

    path('logout/', views.logout_view, name='logout'),

    # Dashboard

    path('', views.dashboard, name='dashboard'),

    # AI Tools

    path('ai/<str:tool>/', views.ai_tool, name='ai_tool'),

    # Saved Content

    path('saved/', views.saved_content, name='saved_content'),

    path(
        'saved/edit/<int:pk>/',
        views.edit_content,
        name='edit_content'
    ),

    path(
        'saved/delete/<int:pk>/',
        views.delete_content,
        name='delete_content'
    ),

    # Planner

    path('planner/', views.planner, name='planner'),

    path(
        'planner/edit/<int:pk>/',
        views.edit_plan,
        name='edit_plan'
    ),

    path(
        'planner/delete/<int:pk>/',
        views.delete_plan,
        name='delete_plan'
    ),

    # Analytics

    path('analytics/', views.analytics, name='analytics'),

    path(
        'analytics/delete/<int:pk>/',
        views.delete_analytics,
        name='delete_analytics'
    ),

    path('api/ai/status/', views.ai_status, name='ai_status'),

]
