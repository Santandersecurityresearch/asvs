
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path(r'', include('home.urls')),
    path('home/', include('home.urls')),
    path('levels/', include('levels.urls')),
    path('help/', include('help.urls'))
]
