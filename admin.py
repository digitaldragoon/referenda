from django.contrib import admin
from referenda.models import *

class ElectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('name',)}
admin.site.register(Election, ElectionAdmin)

class RaceAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('name',)}
    list_display = ('name', 'slug', 'election', 'rank',)
    list_filter = ('election',)
    list_select_related = True
admin.site.register(Race, RaceAdmin)

try:
    from photologue.models import ImageModel
    class BallotCandidatePhotoAdmin(admin.ModelAdmin):
        list_display = ('candidate', 'image', 'date_taken', 'admin_thumbnail')
    admin.site.register(BallotCandidatePhoto, BallotCandidatePhotoAdmin)
except ImportError:
    pass

class BallotCandidateAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'race')
    list_filter = ('race',)
    list_select_related = True
admin.site.register(BallotCandidate, BallotCandidateAdmin)

class WriteInCandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'race')
    list_filter = ('race',)
    list_select_related = True
admin.site.register(WriteInCandidate, WriteInCandidateAdmin)

class ElectionAuthorityAdmin(admin.ModelAdmin):
    list_display = ('user', 'election', 'approved',)
    list_filter = ('election',)
    list_select_related = True
admin.site.register(ElectionAuthority, ElectionAuthorityAdmin)

class SealedVoteAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'poll',)
    list_filter = ('poll',)
    list_select_related = True
admin.site.register(SealedVote, SealedVoteAdmin)
