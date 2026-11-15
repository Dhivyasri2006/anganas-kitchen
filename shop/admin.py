
from django.contrib import admin
from .models import Product, CartItem, Order, OrderItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'category',
        'price',
        'quantity',
    )

    list_filter = ('category',)

    search_fields = ('name', 'description')

    ordering = ('category', 'name')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'product',
        'quantity',
        'added_at',
    )

    search_fields = (
        'user__username',
        'user__email',
        'product__name',
    )

    list_filter = ('added_at',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        'product_name',
        'pack_size',
        'price',
        'quantity',
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number',
        'customer_name',
        'email',
        'phone',
        'total_amount',
        'status',
        'created_at',
    )

    list_filter = ('status', 'created_at')

    search_fields = (
        'order_number',
        'customer_name',
        'email',
        'phone',
    )

    readonly_fields = (
        'order_number',
        'user',
        'total_amount',
        'created_at',
    )

    inlines = [OrderItemInline]

    ordering = ('-created_at',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'product_name',
        'pack_size',
        'price',
        'quantity',
    )

    search_fields = (
        'product_name',
        'order__order_number',
    )

    readonly_fields = (
        'order',
        'product',
        'product_name',
        'pack_size',
        'price',
        'quantity',
    )
