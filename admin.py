from django.contrib import admin
from referenda.models import *

class BallotCandidateAdminInline(admin.TabularInline):
    model = BallotCandidate

class ElectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('name',)}
admin.site.register(Election, ElectionAdmin)

class RaceAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('name',)}
    list_display = ('name', 'slug', 'election', 'rank',)
    list_filter = ('election',)
    list_select_related = True
    inlines = [ BallotCandidateAdminInline, ]
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

class ElectionAuthorityAdmin(admin.ModelAdmin):
    list_display = ('user', 'election', 'approved',)
    list_filter = ('election',)
    list_select_related = True
admin.site.register(ElectionAuthority, ElectionAuthorityAdmin)

class SealedVoteAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'race',)
    list_filter = ('race',)
    list_select_related = True
admin.site.register(SealedVote, SealedVoteAdmin)
