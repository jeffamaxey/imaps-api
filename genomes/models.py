from django.db import models

class Species(models.Model):

    class Meta:
        db_table = "species"
        ordering = ["name"]

    id = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=50)
    latin_name = models.CharField(max_length=50)
    ensembl_id = models.CharField(max_length=50)

    def __str__(self):
        return self.name



class Gene(models.Model):

    class Meta:
        db_table = "genes"
        ordering = ["name"]
    
    name = models.CharField(max_length=20)
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="genes")

    def __str__(self):
        return self.name
