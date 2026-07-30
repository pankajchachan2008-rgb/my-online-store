# management/commands/seed_categories.py
from django.core.management.base import BaseCommand
from products.models import Category # Ensure app name is 'products' or change accordingly

class Command(BaseCommand):
    help = "Seed premium, consolidated categories into the database"

    def handle(self, *args, **kwargs):
        # 🌟 SIRF PREMIUM AUR BROAD CATEGORIES RAKHI HAIN
        categories = [
            "Fashion & Apparel",       # Covers Gents, Ladies, Kids, Footwear
            "Beauty & Personal Care",  # Covers Shaving, Hair, Skin, Oral, Fragrances
            "Home & Lifestyle",        # Covers Detergents, Towels, Lunch Box, Camper
            "Premium Groceries",       # Covers Food and Grocery items
            "Electronics & Tech",      # New premium addition
            "Health & Wellness",       # New premium addition
        ]

        for name in categories:
            obj, created = Category.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created premium category: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Already exists: {name}"))