from django.urls import include, path
from app import views as v

urlpatterns = [
    path("", include("app.urls")),
    path("register", v.register),
    path("shop/", include("app.shop_urls")),
]
