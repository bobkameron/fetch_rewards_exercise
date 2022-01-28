from django.contrib import admin

# Register your models here.

from . models import Payer, Transaction 

admin.site.register(Payer )

admin.site.register(Transaction)
