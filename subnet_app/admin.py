from django.contrib import admin
from subnet_app.models.PingResultLog import PingResultLog
from subnet_app.models.SubnetQueryLog import SubnetQueryLog

admin.site.register(SubnetQueryLog)
admin.site.register(PingResultLog)

