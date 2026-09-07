from django.urls import path
from . import views

urlpatterns = [
    # หน้าหลัก
    path('', views.home, name='home'),

    # รองเท้า
    path('sneakers/', views.sneaker_list, name='sneaker_list'),
    path('sneakers/create/', views.sneaker_create, name='sneaker_create'),
    path('sneakers/update/<int:pk>/', views.sneaker_update, name='sneaker_update'),
    path('sneakers/delete/<int:pk>/', views.sneaker_delete, name='sneaker_delete'),

    # สต็อก
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/create/', views.stock_create, name='stock_create'),
    path('stock/update/<int:pk>/', views.stock_update, name='stock_update'),
    path('stock/delete/<int:pk>/', views.stock_delete, name='stock_delete'),

    # พนักงาน
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/update/<int:pk>/', views.employee_update, name='employee_update'),
    path('employees/delete/<int:pk>/', views.employee_delete, name='employee_delete'),

    # ตะกร้าสินค้า
    path('cart/', views.cart_list, name='cart_list'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:pk>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-orders/delete/<int:pk>/', views.order_delete, name='order_delete'),
    path('admin-carts/', views.admin_carts, name='admin_carts'),
    path('admin-carts/remove/<int:pk>/', views.admin_remove_cart_item, name='admin_remove_cart_item'),
    path('admin-carts/clear/<int:user_id>/', views.admin_clear_cart, name='admin_clear_cart'),
    path('admin-orders/', views.admin_orders, name='admin_orders'),
    path('admin-orders/update/<int:pk>/', views.update_order_status, name='update_order_status'),
    path('admin-orders/delete/<int:pk>/', views.admin_order_delete, name='admin_order_delete'),

    # ระบบสมาชิก (Authentication)
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]