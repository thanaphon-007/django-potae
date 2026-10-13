from django.contrib import admin
from django.utils.html import format_html
from .models import Sneaker, Stock, CartItem, Profile, Order, OrderItem, StoreLocation

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

@admin.register(StoreLocation)
class StoreLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_preview', 'address', 'latitude', 'longitude', 'phone', 'opening_hours', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'address', 'phone', 'opening_hours')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="40" style="object-fit:cover; border-radius:6px;">', obj.image.url)
        return '-'
    image_preview.short_description = 'รูปภาพ'