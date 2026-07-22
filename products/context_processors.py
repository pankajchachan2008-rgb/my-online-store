from .models import Banner

def get_active_banners(request):
    # 'active' ki jagah 'is_active' use karein
    return {'active_banners': Banner.objects.filter(is_active=True)}