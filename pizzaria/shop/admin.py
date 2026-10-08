from django.contrib import admin
from .models import Category, MenuItem, Order
# Register your models here.



class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 0
    fields = ['name', 'price', 'is_popular', 'is_available']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [MenuItemInline]

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_popular', 'is_available']
    list_filter = ['category', 'is_popular', 'is_available']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'is_popular', 'is_available']




@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 
        'customer_name', 
        'customer_phone',
        'total', 
        'status', 
        'payment_method',
        'created_at'
    ]
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['order_number', 'items', 'subtotal', 'total', 'created_at', 'updated_at']
    list_editable = ['status']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_email', 'customer_phone', 'delivery_address')
        }),
        ('Order Details', {
            'fields': ('items', 'subtotal', 'delivery_fee', 'total')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Additional', {
            'fields': ('special_instructions',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Prevent manual creation of orders through admin
        return False