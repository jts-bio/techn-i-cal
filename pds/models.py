from django.db import models

# Create your models here.

class StorageLocation(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name

class Drug(models.Model):
    name = models.CharField(max_length=100)
    dosage = models.FloatField()
    unit_size = models.CharField(max_length=100)