""" URLs for the primary upload and visualization app """

from django.urls import include, path
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

from . import views

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'visualizations', views.JsonConfigViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('', views.Index.as_view()),
    path('index.html', views.Index.as_view(), name='index'),
    path('v/<slug>', views.Visualize.as_view(), name='visualize'),
    path('ve/<slug>', views.VisualizeEmbedded.as_view(), name='visualizeEmbedded'),
    path('upload.html', views.Upload.as_view(), name='upload'),
    path('oembed', views.Oembed.as_view(), name='oembed'),
    path('w/<slug>', views.Wikipedia.as_view(), name='wikipedia'),

    # REST API
    path('api/', include(router.urls)),
    # This is used by the rest_framework to create a login button
    path('api/auth/', include('rest_framework.urls')),
    path('api/auth/get-token', obtain_auth_token),

    # Deprecated but keep old URLs alive indefinitely
    path('visualize=<slug>', views.Visualize.as_view()),
    path('visualizeEmbedded=<slug>', views.VisualizeEmbedded.as_view()),
]
