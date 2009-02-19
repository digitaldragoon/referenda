from django.contrib import admin
from referenda.models import *

class ElectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('name',)}
admin.site.register(Election, ElectionAdmin)

class RaceAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('name',)}
admin.site.register(Race, RaceAdmin)

try:
    from photologue.models import ImageModel
    class BallotCandidatePhotoAdmin(admin.ModelAdmin):
        list_display = ['image', 'date_taken', 'admin_thumbnail']
    admin.site.register(BallotCandidatePhoto, BallotCandidatePhotoAdmin)
except ImportError:
    pass

class BallotCandidateAdmin(admin.ModelAdmin):
    pass
admin.site.register(BallotCandidate, BallotCandidateAdmin)

class WriteInCandidateAdmin(admin.ModelAdmin):
    pass
admin.site.register(WriteInCandidate, WriteInCandidateAdmin)

class ElectionAuthorityAdmin(admin.ModelAdmin):
    pass
admin.site.register(ElectionAuthority, ElectionAuthorityAdmin)

class SealedVoteAdmin(admin.ModelAdmin):
    pass
admin.site.register(SealedVote, SealedVoteAdmin)
