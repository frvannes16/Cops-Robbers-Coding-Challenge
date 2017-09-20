from django.contrib import admin

from challenge.models import Team, Game, Settings, Member

admin.site.register(Team)
admin.site.register(Game)
admin.site.register(Settings)
admin.site.register(Member)
