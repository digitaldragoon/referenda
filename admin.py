from django.contrib import admin
from referenda.models import *

class CandidateAdminInline(admin.TabularInline):
    model = Candidate

class ElectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('name',)}
admin.site.register(Election, ElectionAdmin)

class RaceAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug' : ('name',)}
    list_display = ('name', 'slug', 'election', 'rank',)
    list_filter = ('election',)
    list_select_related = True
    inlines = [ CandidateAdminInline, ]
admin.site.register(Race, RaceAdmin)

try:
    from photologue.models import ImageModel
    class CandidatePhotoAdmin(admin.ModelAdmin):
        list_display = ('candidate', 'image', 'date_taken', 'admin_thumbnail')
    admin.site.register(CandidatePhoto, CandidatePhotoAdmin)
except ImportError:
    pass

class CandidateAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'race')
    list_filter = ('race',)
    list_select_related = True
admin.site.register(Candidate, CandidateAdmin)

class ElectionAuthorityAdmin(admin.ModelAdmin):
    list_display = ('user', 'election',)
    list_filter = ('election',)
    list_select_related = True
admin.site.register(ElectionAuthority, ElectionAuthorityAdmin)

class SealedVoteAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'race',)
    list_filter = ('race',)
    list_select_related = True
admin.site.register(SealedVote, SealedVoteAdmin)

admin.site.register(UnsealedVote)
