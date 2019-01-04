from django.contrib.auth.decorators import login_required
from django.contrib import admin
from django.urls import path
from .views import Index


urlpatterns = [
    path('', login_required(Index.as_view()), name="index"),
    path('admin/', admin.site.urls),
]
