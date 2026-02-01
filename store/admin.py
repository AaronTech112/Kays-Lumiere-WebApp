from django.contrib import admin
from .models import Category, Collection, Product, ProductFAQ

class ProductFAQInline(admin.TabularInline):
    model = ProductFAQ
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock_quantity', 'category', 'is_featured')
    list_filter = ('category', 'collection', 'is_featured')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductFAQInline]
    filter_horizontal = ('recommended_products',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Collection)
