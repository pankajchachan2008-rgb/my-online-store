from .models import Banner

def get_active_banners(request):
    # Sirf wahi banner dikhenge jo 'active' hain
    return {'active_banners': Banner.objects.filter(active=True)}