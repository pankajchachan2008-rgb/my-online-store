from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product

class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Product.objects.all()

    def location(self, obj):
        return reverse('product_detail', args=[obj.id])

class StaticViewSitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return ['product_list', 'about', 'contact', 'login', 'register']

    def location(self, item):
        return reverse(item)