
from django.db import models

from subnet_app.models.SubnetQueryLog import SubnetQueryLog

class PingResultLog(models.Model):
    query_log = models.ForeignKey(
        SubnetQueryLog,
        on_delete=models.CASCADE,
        related_name='results'
        )
    ip_address = models.GenericIPAddressField()
    is_active = models.BooleanField(default=False)
    checked_at = models.DateTimeField(auto_now_add=True)
    rtt = models.FloatField(null=True, blank=True)

    def __str__(self):
        status = "Active" if self.is_active else "Passive"
        return f"{self.ip_address} - {status}"