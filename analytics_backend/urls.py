from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from apps.csvdata import views as csvdata_views
from apps.visualizations import views as visualization_views

# generate the routing for the csvdata endpoints
router = routers.DefaultRouter()
router.register(r'csvdata', csvdata_views.CsvDataViewSet, basename='csvdata')
router.register(r'visualizations', visualization_views.VisualizationViewSet, basename='visualizations')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/', include(router.urls))
]
