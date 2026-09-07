from django.contrib import admin
from .models import Sneaker, Stock, CartItem, Profile, Order, OrderItem

@admin.register(Sneaker)
class SneakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'size', 'price', 'release_date')
    search_fields = ('name', 'brand')

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('sneaker', 'quantity', 'location', 'status', 'last_updated')
    list_filter = ('status', 'location') # เพิ่มตัวกรองข้อมูลด้านขวา

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'sneaker', 'quantity', 'added_at')
    list_filter = ('user',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'first_name', 'last_name', 'phone', 'postal_code', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'phone', 'postal_code', 'address')
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'sneaker', 'quantity', 'price')