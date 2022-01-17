from django.db import models

class Gene(models.Model):

    class Meta:
        db_table = "genes"
        ordering = ["name"]
    
    name = models.CharField(max_length=20)
    species = models.CharField(max_length=2)

    def __str__(self):
        return self.name
