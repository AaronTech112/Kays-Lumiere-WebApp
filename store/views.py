from django.shortcuts import render, get_object_or_404
from .models import Product, Category, Collection

def home_view(request):
    featured_products = Product.objects.filter(is_featured=True)[:8]
    collections = Collection.objects.all()[:3]
    return render(request, 'index.html', {
        'featured_products': featured_products,
        'collections': collections
    })

def shop_view(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
        
    return render(request, 'shop.html', {
        'products': products,
        'categories': categories
    })

def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    recommended_products = product.recommended_products.all()
    faqs = product.faqs.all()
    
    return render(request, 'product.html', {
        'product': product,
        'related_products': related_products,
        'recommended_products': recommended_products,
        'faqs': faqs
    })

def collections_view(request):
    collections = Collection.objects.all()
    return render(request, 'collections.html', {'collections': collections})
