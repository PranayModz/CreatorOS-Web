from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path(
        'ai/<str:tool>/',
        views.ai_tool,
        name='ai_tool'
    ),

    path(
        'saved/',
        views.saved_content,
        name='saved_content'
    ),

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

    path(
        'analytics/',
        views.analytics,
        name='analytics'
    ),
]