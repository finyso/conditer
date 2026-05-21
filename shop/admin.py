from django.contrib import admin
from django.utils.html import format_html
from .models import *

class ProductIngredientInline(admin.TabularInline):
    """Inline для редактирования ингредиентов прямо в продукте"""
    model = ProductIngredient
    extra = 1

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'phone', 'age_display', 'hire_date']
    list_filter = ['position', 'hire_date']
    search_fields = ['name', 'phone', 'email']
    fieldsets = (
        ('Основная информация', {'fields': ('user', 'name', 'position', 'phone', 'email')}),
        ('Личные данные', {'fields': ('date_of_birth', 'photo', 'description')}),
    )
    readonly_fields = ('hire_date',) 
    
    def age_display(self, obj):
        return f"{obj.age()} лет"
    age_display.short_description = 'Возраст'

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'unit', 'is_available', 'created_at']
    list_filter = ['category', 'is_available', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'is_available']
    inlines = [ProductIngredientInline]  

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ['subtotal']

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'employee', 'status', 'order_date', 'delivery_date', 'total_amount'] 
    list_filter = ['status', 'order_date', 'delivery_date', 'employee'] 
    search_fields = ['client__name', 'client__phone', 'delivery_address']
    inlines = [OrderItemInline]
    readonly_fields = ('order_date', 'total_amount')
    
    list_editable = ['status', 'employee']  
    
    actions = ['mark_as_completed']
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = "Отметить как выполненные"

class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'age_display', 'total_spent', 'registered_at']
    search_fields = ['name', 'phone', 'email']
    list_filter = ['registered_at']
    
    def age_display(self, obj):
        return f"{obj.age()} лет"
    age_display.short_description = 'Возраст'

class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'valid_from', 'valid_to', 'is_valid_status', 'used_count']
    list_filter = ['is_active', 'valid_from']
    search_fields = ['code']
    
    def is_valid_status(self, obj):
        return format_html('<span style="color: {};">✓</span>' if obj.is_valid else '✗', 
                          'green' if obj.is_valid else 'red')
    is_valid_status.short_description = 'Действителен'

class ReviewAdmin(admin.ModelAdmin):
    list_display = ['client', 'product', 'rating', 'created_at', 'short_text']
    list_filter = ['rating', 'created_at']
    search_fields = ['client__name', 'text']
    
    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Текст отзыва'

# Регистрация моделей
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Ingredient)
admin.site.register(ProductIngredient) 
admin.site.register(Client, ClientAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(News)
admin.site.register(GlossaryTerm)
admin.site.register(Vacancy)
admin.site.register(Contact)
admin.site.register(CompanyInfo)
from .models import PickupPoint

admin.site.register(PickupPoint)