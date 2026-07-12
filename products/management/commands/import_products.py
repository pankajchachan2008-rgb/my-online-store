import pandas as pd
from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Excel file se products import karne ke liye'

    def handle(self, *args, **kwargs):
        excel_file = 'products.xlsx' # Aapki file ka naam
        
        try:
            # Excel file ko read karein
            df = pd.read_excel(excel_file)
            
            for index, row in df.iterrows():
                # Database me check karein agar SKU pehle se hai toh update karein, nahi toh naya banayein
                product, created = Product.objects.update_or_create(
                    sku=str(row['sku']),
                    defaults={
                        'name': row['name'],
                        'price': row['price'],
                        'stock': row['stock'],
                        'description': row['description'] if pd.notna(row['description']) else ''
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Naya product add hua: {product.name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Product update hua: {product.name}"))
                    
            self.stdout.write(self.style.SUCCESS('Saare products successfully import ho gaye! 🎉'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Error: '{excel_file}' file nahi mili. Kripya check karein."))