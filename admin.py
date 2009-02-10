from django.contrib import admin
from referenda.models import *

class ElectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('name',)}
admin.site.register(Election, ElectionAdmin)

class RaceAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('name',)}
admin.site.register(Race, RaceAdmin)

class BallotCandidateAdmin(admin.ModelAdmin):
    pass
admin.site.register(BallotCandidate, BallotCandidateAdmin)

class WriteInCandidateAdmin(admin.ModelAdmin):
    pass
admin.site.register(WriteInCandidate, WriteInCandidateAdmin)

class ElectionAuthorityAdmin(admin.ModelAdmin):
    pass
admin.site.register(ElectionAuthority, ElectionAuthorityAdmin)
