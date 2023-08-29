"""nutrigo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from api import views

urlpatterns = [
    path(
        "api/calculate/url", views.CalculateFromURL.as_view(), name="calculate-from-url"
    ),
    path(
        "api/calculate/text",
        views.CalculateFromText.as_view(),
        name="calculate-from-text",
    ),
    path("about/", views.AboutView.as_view(), name="about-view"),
    path("", views.IndexView.as_view(), name="index-view"),
]
