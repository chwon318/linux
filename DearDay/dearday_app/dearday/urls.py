from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("diaries/new/", views.conversation_new, name="conversation_new"),
    path("diaries/<int:pk>/", views.conversation_detail, name="conversation_detail"),
    path("diaries/<int:pk>/delete/", views.conversation_delete, name="conversation_delete"),
]
