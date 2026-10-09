from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import api


urlpatterns = [
    path('phones', csrf_exempt(api.PhoneListApi.as_view())),
    path('phones/compare', api.PhoneCompareApi.as_view()),
    path('phones/<int:pk>', csrf_exempt(api.PhoneDetailApi.as_view())),
    path('phones/<int:pk>/favorite', csrf_exempt(api.FavoriteApi.as_view())),
    path('favorites', api.FavoriteListApi.as_view()),
    path('stats', api.StatsApi.as_view()),
    path('health', api.HealthApi.as_view()),
]
