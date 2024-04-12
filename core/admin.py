from django.contrib import admin

from .models import Patient, Professional, Message, AvailabilityOption, GroupOption, CityOption, Session


admin.site.register (Patient)
admin.site.register(Professional)
admin.site.register(Message)
admin.site.register(AvailabilityOption)
admin.site.register(GroupOption)
admin.site.register(CityOption)
admin.site.register(Session)

