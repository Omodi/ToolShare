from django.contrib import admin
from ToolShare.models import Profile, ShareZone, Notification, Shed, Tool, ToolTransaction, Tag, Reservation

admin.site.register(Profile)
admin.site.register(ShareZone)
admin.site.register(Notification)
admin.site.register(Shed)
admin.site.register(Tool)
admin.site.register(ToolTransaction)
admin.site.register(Tag)
admin.site.register(Reservation)