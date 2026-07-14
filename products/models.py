from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# ... (Product, Coupon, Order, OrderItem models wahi rahenge) ...

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    default_address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"

# 🔄 SAFE SIGNALS: Admin login crash nahi hoga
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Sirf normal user ke liye profile banayein, admin ke liye nahi
    if created and not instance.is_superuser and not instance.is_staff:
        CustomerProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Sirf tabhi save karein agar profile exist karti ho
    if hasattr(instance, 'customerprofile'):
        instance.customerprofile.save()