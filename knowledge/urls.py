from django.urls import path
from .views import  index,DocumentUploadView, ChatView
urlpatterns = [
     path('', index),
    path('documents/',DocumentUploadView.as_view()),
    path('chat/',ChatView.as_view()),
]
