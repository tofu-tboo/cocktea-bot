from django.contrib import admin
from django.urls import path
from backend.views import signup, login, logout, delete_account, status, notion_test, update_stock

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/signup/", signup),
    path("api/login/", login),
    path("api/logout/", logout),
    path("api/delete/", delete_account),
    path("", status),
    path("api/", status),
    path("api/notion_test/", notion_test),
    path("api/update-stock/", update_stock)
]