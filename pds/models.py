from django.db import models

# Create your models here.


class Drug(models.Model):
    name       = models.CharField(max_length=100)
    dosage     = models.FloatField()
    unit_size  = models.CharField(max_length=10, choices=(('mg','mg'),('µg','µg'),('gm','gm')))
    
    def __str__ (self):
        return f'{self.name} {self.dosage} {self.unit_size}'
    
class Diluent(models.Model):
    solute          = models.CharField(max_length=100)
    concentration   = models.CharField(max_length=20)
    volume          = models.FloatField()
    
    def __str__ (self):
        return f'{self.solute} {self.concentration} {self.volume}'
    
class Compound(models.Model):
    drugs     = models.ManyToManyField(Drug, related_name='compounds')
    diluent   = models.ForeignKey(Diluent, on_delete=models.CASCADE)
    struct    = models.JSONField()
    
    def __str__(self):
        return f'{" ".join(self.drugs)} in {self.diluent}'
    
