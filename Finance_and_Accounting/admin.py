from django.contrib import admin

# Register your models here.
from Finance_and_Accounting.models import income,total_balance,cuurency,exchagn_money_in_system

# Register your models here.
admin.site.register(income)
admin.site.register(total_balance)
admin.site.register(cuurency)
admin.site.register(exchagn_money_in_system) 