from atexit import register
from django.contrib import admin
from purchase.models import Parchase,BothPartyLedger

admin.site.register(Parchase)
admin.site.register(BothPartyLedger)