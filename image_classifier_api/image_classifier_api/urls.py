from django.contrib import admin
from django.urls import path, include
from classifier import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('classify/', views.ImageClassifierView.as_view()),
]
