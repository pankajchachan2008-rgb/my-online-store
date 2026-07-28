from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product

class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        # Saare products list karein
        return Product.objects.all()

    def lastmod(self, obj):
        # Agar aapke model mein 'updated_at' field hai toh uska use karein, 
        # warna 'created_at' use karein
        return obj.created_at 

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        # Yahan apni website ke sabhi static pages ke 'name' likhein
        return ['home', 'about', 'contact', 'privacy_policy', 'terms_conditions', 'refund_policy']

    def location(self, item):
        return reverse(item)