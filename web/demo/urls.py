from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("send", views.send, name="send"),
    path("help", views.help, name="help"),
    
    path("api/voice", views.voice, name="voice"),
]