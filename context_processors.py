def settings(request):
    from django.conf import settings
    return {'REFERENDA_MEDIA_PREFIX': settings.REFERENDA_MEDIA_PREFIX}
