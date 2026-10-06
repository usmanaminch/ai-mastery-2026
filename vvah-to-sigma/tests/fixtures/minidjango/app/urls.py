from django.urls import path
from . import views

urlpatterns = [
    path("sql_lab", views.sql_lab),
    path("post_lab", views.post_lab),
    path("item/<int:pk>", views.Item.as_view()),
]
