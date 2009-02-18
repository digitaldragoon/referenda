from django.conf import settings

a = list(settings.TEMPLATE_CONTEXT_PROCESSORS)
a.append('referenda.context_processors.settings')

settings.TEMPLATE_CONTEXT_PROCESSORS = tuple(a)
