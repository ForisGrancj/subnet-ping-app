from django.db import models

class SubnetQueryLog(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    subnet_input=models.CharField(max_length=50)
    created_at=models.DateTimeField(auto_now_add=True)
    status=models.CharField(default='PENDING',max_length=20,choices=STATUS_CHOICES)


    def __str__(self):
        return f"{self.subnet_input} - {self.created_at}"
