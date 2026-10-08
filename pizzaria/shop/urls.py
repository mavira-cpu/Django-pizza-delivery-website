from django.urls import path
from . import views

app_name='shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('menu/<slug:slug>/', views.menu_item_detail, name='menu_item_detail'),  # ← Add this
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    
    # Admin URLs
    path('staff/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/orders/', views.admin_orders, name='admin_orders'),
    path('staff/order/<str:order_number>/', views.admin_order_detail, name='admin_order_detail'),
]
