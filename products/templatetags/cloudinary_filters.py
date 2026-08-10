from django import template

register = template.Library()

@register.filter(name='optimize_img')
def optimize_img(url):
    if url and 'res.cloudinary.com' in url and '/upload/' in url:
        # Yeh /upload/ ke baad f_auto,q_auto daal dega
        return url.replace('/upload/', '/upload/f_auto,q_auto/')
    return url