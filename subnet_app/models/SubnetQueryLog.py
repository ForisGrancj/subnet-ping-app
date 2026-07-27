from django.db import models

class SubnetQueryLog(models.Model):
    subnet_input=models.CharField(max_length=50)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subnet_input} - {self.created_at}"
