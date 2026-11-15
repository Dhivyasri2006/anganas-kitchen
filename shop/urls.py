
from django.contrib.auth.views import PasswordResetView
from django.urls import path, include
from . import views

urlpatterns = [

    # Main website pages
    path('', views.home, name='home'),
    path('products/', views.all_products, name='all_products'),
    path('category/<str:category>/', views.category_products, name='category_products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Shopping cart
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Checkout and orders
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path(
        'order-success/<str:order_number>/',
        views.order_success,
        name='order_success'
    ),
    path('my-orders/', views.my_orders, name='my_orders'),

    # Customer account pages
    path('register/', views.register, name='register'),
    path('login/', views.customer_login, name='customer_login'),
    path('logout/', views.customer_logout, name='customer_logout'),
    path('my-profile/', views.my_profile, name='my_profile'),

    # Password reset
    path(
        'accounts/password_reset/',
        PasswordResetView.as_view(
            email_template_name='registration/password_reset_email.txt',
            html_email_template_name='registration/password_reset_email.html',
        ),
        name='password_reset',
    ),

    path('accounts/', include('django.contrib.auth.urls')),
]
