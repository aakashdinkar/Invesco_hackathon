from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from finance import views

urlpatterns = [
    path('', views.homepage),
    path('ticker_info', views.ticker_info),
    path('calculate_ticker_data', views.calculate_ticker_data),
    path('investment_strategy', views.investment_strategy),
]