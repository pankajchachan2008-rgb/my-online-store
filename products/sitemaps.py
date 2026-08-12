from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product

class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        # order_by zaroori hota hai taaki sitemap consistently generate ho
        return Product.objects.all().order_by('-id')

    # 🌟 Product ka URL banane ke liye
    def location(self, item):
        return reverse('product_detail', args=[item.id])

    # 🌟 NAYA FUNCTION (SEO UPGRADE): Google ko batayega ki item kab update hua tha
    def lastmod(self, obj):
        return obj.updated_at

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return ['home', 'about', 'contact', 'privacy_policy', 'terms_conditions', 'refund_policy']

    def location(self, item):
        return reverse(item)