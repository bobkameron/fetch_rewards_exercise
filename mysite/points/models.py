from django.db import models

# Create your models here.


class Payer (models.Model):
    name = models.CharField(max_length = 255, null = False, blank = False, db_index = True )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields= ['name'], name = 'unique_name'),
            ]

class Transaction (models.Model):
    
    payer = models.ForeignKey(Payer, null = False,  db_index = True, \
        on_delete = models.CASCADE , related_name = 'transactions' )

    points = models.IntegerField( null = False)

    timestamp = models.DateTimeField( null = False , db_index = True)
