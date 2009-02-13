def settings(request):
    from django.conf import settings

    dict = {}
    try:
        dict['REFERENDA_MEDIA_PREFIX'] = settings.AREFERENDA_MEDIA_PREFIX
    except AttributeError:
        dict['REFERENDA_MEDIA_PREFIX'] = settings.MEDIA_URL

    return dict
