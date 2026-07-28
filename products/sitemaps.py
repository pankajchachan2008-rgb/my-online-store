from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product

class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        # Yahan sirf '-id' hona chahiye, 'created_at' bilkul nahi
        return Product.objects.all().order_by('-id')

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return ['home', 'about', 'contact', 'privacy_policy', 'terms_conditions', 'refund_policy']

    def location(self, item):
        return reverse(item)