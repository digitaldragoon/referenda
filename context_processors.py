def settings(request):
    from django.conf import settings


    dic = {}
    try:
        dic['REFERENDA_MEDIA_PREFIX'] = settings.REFERENDA_MEDIA_PREFIX
    except AttributeError:
        dic['REFERENDA_MEDIA_PREFIX'] = settings.MEDIA_URL

    return dic
