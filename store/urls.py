from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop_view, name='shop'),
    path('product/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('collections/', views.collections_view, name='collections'),
]
