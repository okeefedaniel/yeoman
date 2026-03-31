from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('collaboration/', include('keel.collaboration.urls')),
    path('', include('yeoman.urls')),
]
