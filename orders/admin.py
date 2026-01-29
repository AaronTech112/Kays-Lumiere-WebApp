from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'status', 'total_amount', 'shipping_fee', 'city', 'created_at']
    list_filter = ['status', 'created_at', 'city']
    search_fields = ['order_id', 'user__username', 'user__email', 'shipping_address']
    inlines = [OrderItemInline]
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered']

    @admin.action(description='Mark selected orders as Paid')
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='Paid')
        self.message_user(request, f'{updated} orders marked as Paid.')

    @admin.action(description='Mark selected orders as Shipped')
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='Shipped')
        self.message_user(request, f'{updated} orders marked as Shipped.')

    @admin.action(description='Mark selected orders as Delivered')
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='Delivered')
        self.message_user(request, f'{updated} orders marked as Delivered.')

    def changelist_view(self, request, extra_context=None):
        from django.db.models import Sum
        
        # Aggregate data for dashboard
        revenue = Order.objects.filter(status__in=['Paid', 'Shipped', 'Delivered']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='Pending').count()
        paid_orders = Order.objects.filter(status='Paid').count()
        
        extra_context = extra_context or {}
        extra_context['total_revenue'] = revenue
        extra_context['total_orders'] = total_orders
        extra_context['pending_orders'] = pending_orders
        extra_context['paid_orders'] = paid_orders
        
        return super().changelist_view(request, extra_context=extra_context)

admin.site.register(Cart)
admin.site.register(CartItem)
