from django.shortcuts import render,redirect,HttpResponse
from.forms import *
from django.contrib import messages
from itertools import chain
from django.db.models import Sum
from django.db.models import Value, CharField
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.ttfonts import TTFont
from reportlab import pdfbase
from django.contrib.staticfiles.storage import staticfiles_storage
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from django.db.models import OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.db.models import OuterRef, Subquery, Sum, F, Value
from itertools import chain
from django.db.models import Value, CharField
from Order.models import sale_item_part
from purchase.models import Parchase
from expenses.models import FixedExpense
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.http import HttpResponse
from django.contrib.staticfiles.storage import staticfiles_storage
from bidi.algorithm import get_display
import arabic_reshaper
import os
from Customer.models import Loan,SLoan
from django.db import transaction
from purchase.models import BothPartyLedger





def malle_wa_mahaseba(request):
   
    collaborators  = coolaborators.objects.all()
    loans = Loan.objects.all().order_by('id')
    bot_ledger_entry = BothPartyLedger.objects.filter(entry_type__in=['sale', 'receive_from_partner'])
    purchase_both_ledger_entry = BothPartyLedger.objects.filter(entry_type__in=['purchase', 'pay_to_partner'])
    

    customer_ids = loans.values_list('customer_id', flat=True).distinct()
    
    customer_totals = {}
    
    for customer_id in customer_ids:
        customer_loan = Loan.objects.filter(customer_id=customer_id)
        sale_ids = customer_loan.values_list('sale_id', flat=True)
        
        total_sale_amount = sale_item_part.objects.filter(id__in=sale_ids).aggregate(
            paid_amount_for_every_record_sum=Sum('paid_amount_for_every_record') 
        )['paid_amount_for_every_record_sum'] or 0

        customer_loan_with_notes_sum = Loan.objects.filter(
            customer_id=customer_id,
            status='پرداخت شده'
        ).exclude(notes__isnull=True).exclude(notes='').aggregate(
            total_amount_sum=Sum('amount')
        )['total_amount_sum'] or 0

        find_all_total_sale_amount = round(total_sale_amount + customer_loan_with_notes_sum)
        customer_totals[customer_id] = find_all_total_sale_amount


    sloans = SLoan.objects.all().order_by('id')
    supp_ids = sloans.values_list('customer_id', flat=True).distinct()
    supp_totals = {}
    for supp_id in supp_ids:
        supploans = SLoan.objects.filter(customer_id=supp_id)
        suppliar_id = supploans.values_list('sale_id', flat=True)

        total_sale_amount_sup = Parchase.objects.filter(id__in=suppliar_id).aggregate(
            paid_amount_sum=Sum('paid_amount')
        )['paid_amount_sum'] or 0 

        customer_loan_sum_supp = SLoan.objects.filter(
            customer_id=supp_id,
            status='پرداخت شده'
        ).exclude(
            notes__isnull=True  
        ).exclude(
            notes=''  
        ).aggregate(
            total_amount_sum_sipp=Sum('amount')
        )['total_amount_sum_sipp'] or 0
        find_all_total_sale_amount_supp = round(total_sale_amount_sup + customer_loan_sum_supp)
        supp_totals[supp_id] = find_all_total_sale_amount_supp

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        try:
            with transaction.atomic(): 
                if form_type == 'income':
                    my_form = incomeForm(request.POST)
                    if my_form.is_valid():
                        instance = my_form.save(commit=False)
                        find_the_user = my_form.cleaned_data.get('olabrate')
                        find_id = find_the_user.id
                        money = my_form.cleaned_data.get('income_amount')
                        currency_type = my_form.cleaned_data.get('curr')
                        curr_id = currency_type.id
                        find_the_name = currency_type.curr_name
                        exchange_rate = my_form.cleaned_data.get('exchagne_rate')
                        find_the_last_record = income.objects.filter(olabrate=find_id, curr=curr_id).last()
                        
                        try:
                            find_the_bolean = find_the_last_record.blooelean_field
                        except:
                            find_the_bolean = None
                            
                        if find_the_last_record:
                            if find_the_name == 'افغانی':
                                instance.is_income_or_outcome = 'دریافت'
                                my_data = total_balance.objects.select_for_update().first()
                                find_total_system_money = my_data.total_money_in_system
                                sum = find_total_system_money + money
                                my_data.total_money_in_system = sum
                                instance.exchagne_rate = 0
                                instance.exchanged_moneey = money
                                
                                if find_the_bolean == True:
                                    find_the_last = find_the_last_record.total_incme_with_last_record
                                    sum_with_the_last_record = find_the_last + money
                                    instance.total_incme_with_last_record = sum_with_the_last_record
                                    instance.blooelean_field = True
                                elif find_the_bolean == None:
                                    find_the_last = find_the_last_record.total_incme_with_last_record
                                    sum_with_the_last_record = find_the_last + money
                                    instance.total_incme_with_last_record = sum_with_the_last_record
                                    instance.blooelean_field = True                
                                else:
                                    find_the_last = find_the_last_record.total_incme_with_last_record
                                    if money > find_the_last:
                                        sum_with_the_last_record = abs(find_the_last - money)
                                        instance.total_incme_with_last_record = sum_with_the_last_record
                                        instance.blooelean_field = True
                                    elif money == find_the_last: 
                                        sum_with_the_last_record = find_the_last - money
                                        instance.total_incme_with_last_record = sum_with_the_last_record
                                        instance.blooelean_field = None
                                    else:
                                        sum_with_the_last_record = find_the_last - money
                                        instance.total_incme_with_last_record = sum_with_the_last_record
                                        instance.blooelean_field = False
                                
                                my_data.save()
                            else:
                                instance.is_income_or_outcome = 'دریافت'
                                find_the_other_cuur_balance = cuurency.objects.select_for_update().get(curr_name=currency_type)
                                fidn_the_balance = find_the_other_cuur_balance.balance
                                sum_the_balance = fidn_the_balance + money
                                find_the_other_cuur_balance.balance = sum_the_balance
                                find_the_other_cuur_balance.save() 
                                instance.exchagne_rate = exchange_rate 
                                instance.exchanged_moneey = money * (exchange_rate if exchange_rate else 0)
                                
                                if find_the_bolean == True:
                                    find_the_last = find_the_last_record.total_incme_with_last_record
                                    sum_with_the_last_record = find_the_last + money
                                    instance.total_incme_with_last_record = sum_with_the_last_record
                                    instance.blooelean_field = True    
                                elif find_the_bolean == None:
                                    find_the_last = find_the_last_record.total_incme_with_last_record
                                    sum_with_the_last_record = find_the_last + money
                                    instance.total_incme_with_last_record = sum_with_the_last_record
                                    instance.blooelean_field = True                
                                else:
                                    find_the_last = find_the_last_record.total_incme_with_last_record
                                    if money > find_the_last:
                                        sum_with_the_last_record = abs(find_the_last - money)
                                        instance.total_incme_with_last_record = sum_with_the_last_record
                                        instance.blooelean_field = True
                                    elif money == find_the_last:
                                        sum_with_the_last_record = find_the_last - money
                                        instance.total_incme_with_last_record = sum_with_the_last_record
                                        instance.blooelean_field = None
                                    else:
                                        sum_with_the_last_record = find_the_last - money
                                        instance.total_incme_with_last_record = sum_with_the_last_record
                                        instance.blooelean_field = False
                                
                                
                        else:
                            if find_the_name == 'افغانی':
                                instance.is_income_or_outcome = 'دریافت'
                                my_data = total_balance.objects.select_for_update().first()
                                find_total_system_money = my_data.total_money_in_system
                                sum = find_total_system_money + money
                                my_data.total_money_in_system = sum
                                instance.exchagne_rate = 0
                                instance.exchanged_moneey = money
                                instance.total_incme_with_last_record = money
                                instance.blooelean_field = True
                                my_data.save()
                            else:
                                instance.is_income_or_outcome = 'دریافت'
                                find_the_other_cuur_balance = cuurency.objects.select_for_update().get(curr_name=currency_type)
                                fidn_the_balance = find_the_other_cuur_balance.balance
                                sum_the_balance = fidn_the_balance + money
                                find_the_other_cuur_balance.balance = sum_the_balance
                                instance.exchagne_rate = exchange_rate 
                                instance.exchanged_moneey = money * (exchange_rate if exchange_rate else 0)
                                instance.total_incme_with_last_record = money
                                instance.blooelean_field = True
                                find_the_other_cuur_balance.save()
                        
                        instance.save()
                        my_form.save()
                        messages.success(request, 'دریافت پول موفقانه اجرا شد')
                        return redirect('Finance_and_Accounting:malle_wa_mahaseba')
                    else:
                        messages.warning(request, 'مشکل موجود بوده دریافت جدید ثبت نشد')
                        return redirect('Finance_and_Accounting:malle_wa_mahaseba')

                elif form_type == 'outcome':
                    my_form = out_comeForm(request.POST)
                    if my_form.is_valid():
                        instance = my_form.save(commit=False)
                        find_the_user = my_form.cleaned_data.get('olabrate')
                        find_id = find_the_user.id
                        money = my_form.cleaned_data.get('income_amount')
                        currency_type = my_form.cleaned_data.get('curr')
                        curr_id = currency_type.id
                        find_the_name = currency_type.curr_name
                        exchange_rate = my_form.cleaned_data.get('exchagne_rate')
                        find_the_last_record = income.objects.filter(olabrate=find_id, curr=curr_id).last()
                        
                        try:
                            find_the_bolean = find_the_last_record.blooelean_field
                        except:
                            find_the_bolean = None
                            
                        if find_the_last_record:
                            if find_the_name == 'افغانی':
                                instance.is_income_or_outcome = 'پرداخت'
                                my_data = total_balance.objects.select_for_update().first()
                                find_total_system_money = my_data.total_money_in_system
                                
                                if money > find_total_system_money:
                                    raise ValueError('پول که میخواهید پرداخت کنید بیشتر از مجموهه پول موجودی در سیستم بوده و پرداخت اجرا نمیگردد')
                                
                                mines = find_total_system_money - money
                                my_data.total_money_in_system = mines
                                instance.exchagne_rate = 0
                                instance.exchanged_moneey = money
                                
                                if find_the_bolean == True:
                                    find_the_last = find_the_last_record.total_incme_with_last_record
                                    if money > find_the_last:
                                        sum_with_the_last_record = abs(find_the_last - money)
                                        instance.total_incme_with_last_record = sum_with_the_last_record
                                        instance.blooelean_field = False
                                    elif money == find_the_last:
                                        sum_with_the_last_record = find_the_last - money
                                        instance.total_incme_with_last_record = sum_with_the_last_record
                                        instance.blooelean_field = None
                                    else:
                                        sum_with_the_last_record = find_the_last - money
                                        instance.total_incme_with_last_record = sum_with_the_last_record
                                        instance.blooelean_field = True
                                elif find_the_bolean == None:
                                    find_the_last = find_the_last_record.total_incme_with_last_record
                                    sum_with_the_last_record = find_the_last + money
                                    instance.total_incme_with_last_record = sum_with_the_last_record
                                    instance.blooelean_field = False
                                else:
                                    find_the_last = find_the_last_record.total_incme_with_last_record
                                    sum_with_the_last_record = find_the_last + money
                                    instance.total_incme_with_last_record = sum_with_the_last_record
                                    instance.blooelean_field = False
                                
                                my_data.save()
                            else:
                                instance.is_income_or_outcome = 'پرداخت'
                                find_the_other_cuur_balance = cuurency.objects.select_for_update().get(curr_name=currency_type)
                                fidn_the_balance = find_the_other_cuur_balance.balance
                                
                                if money > fidn_the_balance:
                                    raise ValueError('پول که میخواهید پرداخت کنید بیشتر از مجموهه پول موجودی در سیستم بوده و پرداخت اجرا نمیگردد')
                                
                                sum_the_balance = fidn_the_balance - money
                                find_the_other_cuur_balance.balance = sum_the_balance
                                instance.exchagne_rate = exchange_rate 
                                instance.exchanged_moneey = money * (exchange_rate if exchange_rate else 0)
                                
                                if find_the_bolean == True:
                                    find_the_last = find_the_last_record.total_incme_with_last_record
                                    if money > find_the_last:
                                        sum_with_the_last_record = abs(find_the_last - money)
                                        instance.total_incme_with_last_record = sum_with_the_last_record
                                        instance.blooelean_field = False
                                    elif money == find_the_last:
                                        sum_with_the_last_record = find_the_last - money
                                        instance.total_incme_with_last_record = sum_with_the_last_record
                                        instance.blooelean_field = None
                                    else:
                                        sum_with_the_last_record = find_the_last - money
                                        instance.total_incme_with_last_record = sum_with_the_last_record
                                        instance.blooelean_field = True
                                elif find_the_bolean == None:
                                    find_the_last = find_the_last_record.total_incme_with_last_record
                                    sum_with_the_last_record = find_the_last + money
                                    instance.total_incme_with_last_record = sum_with_the_last_record
                                    instance.blooelean_field = False
                                else:
                                    find_the_last = find_the_last_record.total_incme_with_last_record
                                    sum_with_the_last_record = find_the_last + money
                                    instance.total_incme_with_last_record = sum_with_the_last_record
                                    instance.blooelean_field = False
                                
                                find_the_other_cuur_balance.save()
                        else:
                            if find_the_name == 'افغانی':
                                instance.is_income_or_outcome = 'پرداخت'
                                my_data = total_balance.objects.select_for_update().first()
                                find_total_system_money = my_data.total_money_in_system
                                
                                if money > find_total_system_money:
                                    raise ValueError('پول که میخواهید پرداخت کنید بیشتر از مجموهه پول موجودی در سیستم بوده و پرداخت اجرا نمیگردد')
                                
                                mines = find_total_system_money - money
                                my_data.total_money_in_system = mines
                                instance.exchagne_rate = 0
                                instance.exchanged_moneey = money
                                instance.total_incme_with_last_record = money
                                instance.blooelean_field = False
                                my_data.save()
                            else:
                                instance.is_income_or_outcome = 'پرداخت'
                                find_the_other_cuur_balance = cuurency.objects.select_for_update().get(curr_name=currency_type)
                                fidn_the_balance = find_the_other_cuur_balance.balance
                                
                                if money > fidn_the_balance:
                                    raise ValueError('پول که میخواهید پرداخت کنید بیشتر از مجموهه پول موجودی در سیستم بوده و پرداخت اجرا نمیگردد')
                                
                                sum_the_balance = fidn_the_balance - money
                                find_the_other_cuur_balance.balance = sum_the_balance
                                instance.exchagne_rate = exchange_rate 
                                instance.exchanged_moneey = money * (exchange_rate if exchange_rate else 0)
                                instance.total_incme_with_last_record = money
                                instance.blooelean_field = False
                                find_the_other_cuur_balance.save()
                        
                        instance.save()
                        my_form.save()
                        messages.success(request, 'پرداخت پول موفقانه اجرا شد')
                        return redirect('Finance_and_Accounting:malle_wa_mahaseba')
                    else:
                        messages.warning(request, 'مشکل موجود بوده پرداخت جدید ثبت نشد')
                        return redirect('Finance_and_Accounting:malle_wa_mahaseba')
        
        except ValueError as e:
            messages.warning(request, str(e))
            return redirect('Finance_and_Accounting:malle_wa_mahaseba')
        except Exception as e:
            messages.error(request, f'خطای سیستمی: {str(e)}')
            return redirect('Finance_and_Accounting:malle_wa_mahaseba')
    else:

        find_all_sale_money = sale_item_part.objects.aggregate(total_should_paid=Sum('should_paid'))
        total_should_paid = find_all_sale_money['total_should_paid'] or 0


        find_all_sale_money = Parchase.objects.aggregate(total_parchase_paid=Sum('total_unit'))
        total_parchase_paid = find_all_sale_money['total_parchase_paid'] or 0


        find_all_currency = cuurency.objects.exclude(curr_name="افغانی")
        all_incoming_money = income.objects.all()
        total_income = income.objects.filter(is_income_or_outcome='دریافت')

         
        income_sums = (
            income.objects.filter(is_income_or_outcome='دریافت')
            .values('curr', 'curr__curr_name')
            .annotate(total_income=Sum('income_amount'))
        )

        outcomesum = (income.objects.filter(is_income_or_outcome='پرداخت').values('curr','curr__curr_name').annotate(total_outcome=Sum('income_amount')))
        all_outgoing_money = outcome.objects.all()
        total_out_come = outcome.objects.aggregate(total=Sum('out_come_amount'))['total'] or 0

        find_all_sale_money = FixedExpense.objects.aggregate(total_expenses_paid=Sum('total_amount'))
        total_expenses_paid = find_all_sale_money['total_expenses_paid'] or 0
        all_incoming_money = all_incoming_money.annotate(transaction_type=models.Value('income', output_field=models.CharField()))
        all_outgoing_money = all_outgoing_money.annotate(transaction_type=models.Value('outcome', output_field=models.CharField()))

        all_transactions = chain(all_incoming_money, all_outgoing_money)

        all_collaborator = coolaborators.objects.all().count()
        my_data = total_balance.objects.first()
        if not my_data:
            my_data = total_balance.objects.create(total_money_in_system=0)
        my_form = incomeForm() 
        all_datas = income.objects.all().order_by('id')
        
        out_come_form = out_comeForm() 
        context = { 
            'all_datas':all_datas,
            'my_form':my_form,
            'my_data':my_data,
            'all_transactions': all_transactions,
            'out_come_form':out_come_form,
            'all_collaborator':all_collaborator,
            'total_income':total_income,
            'total_out_come':total_out_come,
            'find_all_currency':find_all_currency,
            'total_should_paid':total_should_paid,
            'total_parchase_paid':total_parchase_paid,
            'total_expenses_paid':total_expenses_paid,
            'income_sums':income_sums,
            'outcomesum':outcomesum,
            'loans':loans,
            'customer_totals': customer_totals,
            'sloans':sloans,
            'supp_totals':supp_totals,
            'collaborators':collaborators,
            'bot_ledger_entry':bot_ledger_entry,
            'purchase_both_ledger_entry':purchase_both_ledger_entry,

        }
    return render(request, 'finanace/public_page.html',context)







def currency(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():  
                my_form = cuurencyForm(request.POST) 
                if my_form.is_valid():
                    my_form.save()
                    messages.success(request, 'واحد پولی جدید موفقانه ثبت شد')
                    return redirect('Finance_and_Accounting:currency')
                else:
                    messages.warning(request, 'مشکل موجود بوده واحد پولی جدید ثبت نشد')
                    return redirect('Finance_and_Accounting:currency')
                    
        except Exception as e:
            messages.error(request, f'خطای سیستمی: {str(e)}')
            return redirect('Finance_and_Accounting:currency')
    else:
        all_date = cuurency.objects.all()
        my_form = cuurencyForm()

        context = {
            'all_date':all_date,
            'my_form':my_form,

        }
    return render(request, 'finanace/currency.html',context)



def collaborates(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():  
                my_form = coolaboratorsForm(request.POST)
                if my_form.is_valid():
                    name = my_form.cleaned_data["name_opf"]
                    find_dame_collaboraores = coolaborators.objects.filter(name_opf=name)
                    if find_dame_collaboraores.exists():
                        messages.warning(request, ' شریک به این اسم موجود است لطفا شخصی جدیدی ثبت نمایید')
                        return redirect('Finance_and_Accounting:collaborates')
                    else:
                        my_form.save()
                    messages.success(request, ' شریک جدید موفقانه ثبت شد')
                    return redirect('Finance_and_Accounting:collaborates')
                else:
                    messages.warning(request, 'مشکل موجود بوده شریک جدید ثبت نشد')
                    return redirect('Finance_and_Accounting:collaborates')  
        except Exception as e:
            messages.error(request, f'خطای سیستمی: {str(e)}')
            return redirect('Finance_and_Accounting:currency')
    else:
        all_data = coolaborators.objects.all()
        last_boolean_values = {}

        for collab in all_data:
            last_income = income.objects.filter(olabrate=collab).last()
            if last_income:
                last_boolean_values[collab.id] = last_income.blooelean_field
            else:
                last_boolean_values[collab.id] = None
        

        my_form = coolaboratorsForm() 
        context = { 
            'my_form':my_form,
            'all_data':all_data,
            'last_boolean_values':last_boolean_values,
        }
    return render(request, 'finanace/coola.html',context)
from django.db.models import Max
def partners_loan_amount(request):
    loan_data = []

    all_collaborators = coolaborators.objects.all()

    for partner in all_collaborators:
        latest_currency_records = income.objects.filter(
            olabrate=partner
        ).values(
            'curr'
        ).annotate(
            last_id=Max('id')
        )

        latest_ids = [item['last_id'] for item in latest_currency_records]

        latest_records = income.objects.filter(
            id__in=latest_ids,
            blooelean_field=False
        ).select_related('curr')

        if latest_records.exists():
            loan_data.append({
                'partner': partner,
                'records': latest_records,
            })

    context = {
        'loan_data': loan_data,
    }
    return render(request, 'finanace/partner_loan_records.html', context)

def loan_collaborate_partners(request):
    loan_data = []

    all_collaborators = coolaborators.objects.all()

    for partner in all_collaborators:
        latest_currency_records = income.objects.filter(
            olabrate=partner
        ).values(
            'curr'
        ).annotate(
            last_id=Max('id')
        )

        latest_ids = [item['last_id'] for item in latest_currency_records]

        latest_records = income.objects.filter(
            id__in=latest_ids,
            blooelean_field=False
        ).select_related('curr')

        if latest_records.exists():
            loan_data.append({
                'partner': partner,
                'records': latest_records,
            })

    context = {
        'loan_data': loan_data,
    }
    return render(request, 'finanace/partner_print_col.html', context)




def edit_collaborators(request, id):
    find_collaborator = coolaborators.objects.get(id=id)
    form = coolaboratorsForm(request.POST or None, instance=find_collaborator)
    if request.method == 'POST':
        try:
            with transaction.atomic():  
                if form.is_valid():
                    form.save()
                    messages.success(request, 'اطلاعات شریک موفقانه ویرایش شد')
                    return redirect('Finance_and_Accounting:collaborates')
                else:
                    messages.warning(request, 'مشکل موجود بوده تغیرات ثبت نشد')
        except Exception as e:
            messages.error(request, f'خطای سیستمی: {str(e)}')
            return redirect('Finance_and_Accounting:collaborates')

    context = {
        'form': form,
        'find_collaborator': find_collaborator
    }
    return render(request, 'finanace/Edit/edit_collaborators.html', context)

from django.shortcuts import redirect, get_object_or_404

@transaction.atomic
def delete_collaborators(request, id):
    try:
        record = get_object_or_404(coolaborators, id=id)
        income_exists = income.objects.filter(olabrate_id=id).exists()
        outcome_exists = outcome.objects.filter(olabrate_id=id).exists()

        if income_exists or outcome_exists:
            messages.warning(request, 'شریک دارای سوابق مالی است و نمی‌تواند حذف شود')
        else:
            record.delete()
            messages.success(request, 'شریک موفقانه حذف شد')

    except Exception as e:
        transaction.set_rollback(True)
        messages.error(request, f'خطا هنگام حذف شریک: {str(e)}')

    return redirect('Finance_and_Accounting:collaborates')





def col_balance(request, id):
    from django.db.models import Max
    find_collaborator = coolaborators.objects.get(id=id)
    find_collaborator_id = find_collaborator.id
    all_income = income.objects.filter(olabrate_id=find_collaborator_id, is_income_or_outcome='دریافت').aggregate(total_income=Sum('income_amount'))['total_income'] or 0
    all_out_come = income.objects.filter(olabrate_id=find_collaborator_id, is_income_or_outcome='پرداخت').aggregate(out_come=Sum('income_amount'))['out_come'] or 0
    transactions_with_totals = income.objects.filter(olabrate_id=find_collaborator,curr=1).order_by("id")


    find_the_dollar_in_afghani = income.objects.filter(olabrate_id=find_collaborator,is_income_or_outcome='دریافت',curr=2).aggregate(total_exchanged_money=Sum('exchanged_moneey'))
    total_exchanged_money = find_the_dollar_in_afghani['total_exchanged_money'] or 0

    find_the_dollar_in_afghani_pardakht = income.objects.filter(olabrate_id=find_collaborator,is_income_or_outcome='پرداخت',curr=2).aggregate(total_exchanged_pardakht_money=Sum('exchanged_moneey'))
    total_exchanged_pardakht_money = find_the_dollar_in_afghani_pardakht['total_exchanged_pardakht_money'] or 0
    mines_amount = total_exchanged_money - total_exchanged_pardakht_money
    find_borrow = income.objects.filter(olabrate_id=find_collaborator) \
            .values('curr') \
            .annotate(last_id=Max('id')) 
    latest_records = income.objects.filter(id__in=[item['last_id'] for item in find_borrow])
    total_income_list = []
    blooelean_field_status = None 
    for record in latest_records:
        total_income_value = f"{record.total_incme_with_last_record} ({record.curr.curr_name})"
        
        if record.blooelean_field is True:
            status_label = "ما قرضدار هستیم"
        elif record.blooelean_field is None:
            status_label = "برابر"
        else:
            status_label = " قرضدار است"
        
        total_income_list.append(f"{total_income_value} - {status_label}")  

    total_income_str = ', '.join(total_income_list) 

    running_total = 0 
    for transaction in transactions_with_totals:
        if transaction.is_income_or_outcome == "دریافت":
            running_total += transaction.income_amount
        elif transaction.is_income_or_outcome == "پرداخت": 
             running_total -= transaction.income_amount
        transaction.running_total = running_total 

    cur_balance = all_income - all_out_come

    context = {
        'transactions_with_totals': transactions_with_totals,
        'find_collaborator': find_collaborator,
        'all_income': all_income,
        'all_out_come': all_out_come,
        'all_transactions': transactions_with_totals,
        'cur_balance': cur_balance,
        'total_income_str': total_income_str,
        'status_label': status_label,
        'find_collaborator': find_collaborator,
        'cur_balance': total_income_str,
        'mines_amount':mines_amount,
    }
    return render(request, 'finanace/collaborators/collaborators_balance_sheet.html', context)



def find_folar_records(request,id):
    find_collaborator = coolaborators.objects.get(id=id)
    find_collaborator_id = find_collaborator.id
    transactions_with_totals = income.objects.filter(olabrate_id=find_collaborator_id,curr=2).order_by("id")
    context = { 
        'find_collaborator':find_collaborator,
        'transactions_with_totals':transactions_with_totals,
    }
    return render(request, 'finanace/dollar.html',context)



def all_records(request,id):
    transactions_with_totals = income.objects.filter(olabrate_id=id).order_by("id")
    context = {
        'transactions_with_totals':transactions_with_totals,
    }
    return render(request, 'finanace/all.html',context)




def reshape_text(text):
    """Reshape Persian text for correct display in PDF"""
    return get_display(arabic_reshaper.reshape(text))

def generate_pdf(request, id):
    find_collaborator = coolaborators.objects.get(id=id)
    all_income = income.objects.filter(olabrate_id=id, is_income_or_outcome='دریافت').aggregate(total_income=Sum('income_amount'))['total_income'] or 0
    all_out_come = income.objects.filter(olabrate_id=id, is_income_or_outcome='پرداخت').aggregate(out_come=Sum('income_amount'))['out_come'] or 0
    transactions = income.objects.filter(olabrate_id=id)

    running_total = 0
    transactions_with_totals = []
    for transaction in transactions:
        if transaction.is_income_or_outcome == "دریافت":
            running_total += transaction.income_amount
        elif transaction.is_income_or_outcome == "پرداخت":
            running_total -= transaction.income_amount
        transactions_with_totals.append([ 
            
            str(running_total),
            reshape_text(transaction.curr.curr_name or ""),
            str(transaction.income_amount),
            reshape_text(transaction.descriiption or ""),
            str(transaction.rec_date),
            reshape_text(transaction.is_income_or_outcome),
            str(transaction.id),
        ])

    cur_balance = all_income - all_out_come

    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="collaborator_{id}_balance_sheet.pdf"'

    # Register a better font for Persian/Arabic text
    font_path = staticfiles_storage.path('fonts/Amiri-Regular.ttf')  # Relative path to the font file
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Amiri', font_path))
        font_name = 'Amiri'
    else:
        # Fallback to a default font if Amiri is not found
        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        font_name = 'Arial'

    # Create a PDF document
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []

    # Custom Paragraph Style for Persian/Arabic text
    styles = getSampleStyleSheet()
    persian_style = ParagraphStyle(
        name='PersianStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        alignment=1,  # Center alignment
    )

    # Title
    title_text = f"محاسبه مالی {find_collaborator.name_opf}"
    title = Paragraph(reshape_text(title_text), persian_style)
    elements.append(title)
    elements.append(Spacer(1, 20))  # Add space after the title

    # Table Data
    headers = [
        
        reshape_text("مجموعه"),
        reshape_text("واحد پولی"), 
        reshape_text("مقدار"),
        reshape_text("توضیحات"), 
        reshape_text("تاریخ"),
        reshape_text("نوعیت"),
        reshape_text("شماره"),
    ]
    data = [headers] + transactions_with_totals

    # Create a Table
    table = Table(data, colWidths=[100, 80, 100, 80, 80, 60])  # Adjust column widths as needed
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Header background color
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center align all cells
        ('FONTNAME', (0, 0), (-1, 0), font_name),  # Header font
        ('FONTNAME', (0, 1), (-1, -1), font_name),  # Data font
        ('FONTSIZE', (0, 0), (-1, -1), 10),  # Font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Header padding
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Data row background color
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Grid lines
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))  # Add space after the table

    # Add current balance

    # Build the PDF
    doc.build(elements)
    return response


def edit_col_balance(request, id):
    find_record = income.objects.get(id=id)
    if find_record.is_income_or_outcome == 'دریافت':
        form = incomeForm(request.POST or None, instance=find_record)
        form_type = 'income'
    else:
        form = incomeForm(request.POST or None, instance=find_record)
        form_type = 'outcome'

    if request.method == 'POST':
        if form.is_valid():
            if form_type == 'income':
                money = form.cleaned_data.get('income_amount')
                find_record.income_amount = money
                my_data = total_balance.objects.first()
                my_data.total_money_in_system += money
                my_data.save()
                form.save()
                all_income = 0
                all_incoming_money = income.objects.filter(olabrate_id=id)
                for i in all_incoming_money:

                    all_income_money = i.income_amount
                    all_income += all_income_money

                messages.success(request, 'اصل ریکارد برای دریافت پول ثبت شده بود و قیمت جدید شما در سیستم محاسبه گردید.')
                return redirect('Finance_and_Accounting:col_balance', id=find_record.olabrate_id)
            elif form_type == 'outcome':
                money = form.cleaned_data.get('income_amount')
                find_record.income_amount = money

                my_data = total_balance.objects.first()
                my_data.total_money_in_system -= money
                my_data.save()
                form.save()
                all_out_come = 0
                all_out_come_money = income.objects.filter(olabrate_id=id)
                for i in all_out_come_money:
                    all_out_come_money = i.income_amount
                    all_out_come += all_out_come_money
                messages.success(request, 'اصل ریکارد برای پرداخت پول ثبت شده بود و قیمت جدید شما در سیستم محاسبه گردید.')
                return redirect('Finance_and_Accounting:col_balance', id=find_record.olabrate_id)
        else:
            messages.warning(request, 'مشکل موجود بوده تغیرات ثبت نشد')

    context = {
        'form': form,
        'find_record': find_record,
        'form_type': form_type,
    }
    return render(request, 'finanace/collaborators/edit_col_balance.html', context)


def delete_col_balance(request, id):
    my_data = total_balance.objects.first()
    find_data = income.objects.get(id=id) 
    

    if find_data.is_income_or_outcome == 'دریافت':
        if find_data.curr.curr_name == 'افغانی':
            record = income.objects.get(id=id)
            find_the_user = record.olabrate
            find_date_curr = record.curr
            amount = find_data.income_amount
            find_the_last_record = income.objects.filter(olabrate=find_the_user,curr=find_date_curr).last()
            find_the_total_of_last = find_the_last_record.total_incme_with_last_record
            find_the_last_record.total_incme_with_last_record -= amount
            my_data = total_balance.objects.first()
            my_data.total_money_in_system -= amount
            find_the_last_record.save() 
            my_data.save()
            record.delete() 
            messages.success(request, 'دریافت پول موفقانه حذف شد')
            return redirect('Finance_and_Accounting:malle_wa_mahaseba')
        else:
            record = income.objects.get(id=id)
            amount = record.income_amount
            curr = record.curr
            find_the_user = record.olabrate
            find_date_curr = record.curr
            find_the_last_record = income.objects.filter(olabrate=find_the_user,curr=find_date_curr).last()
            find_the_total_of_last = find_the_last_record.total_incme_with_last_record
            find_the_last_record.total_incme_with_last_record -= amount

            find_the_currin_currency = cuurency.objects.get(curr_name=curr)
            find_the_total_amount = find_the_currin_currency.balance
            find_the_currin_currency.balance -= amount
            find_the_last_record.save()
            find_the_currin_currency.save()
            record.delete()
            messages.success(request, 'دریافت پول موفقانه حذف شد')
            return redirect('Finance_and_Accounting:malle_wa_mahaseba')

    elif find_data.is_income_or_outcome == 'پرداخت':
        if find_data.curr.curr_name == 'افغانی':
            record = income.objects.get(id=id)
            find_the_user = record.olabrate
            amount = find_data.income_amount
            find_date_curr = record.curr
            find_the_last_record = income.objects.filter(olabrate=find_the_user,curr=find_date_curr).last()
            find_the_total_of_last = find_the_last_record.total_incme_with_last_record
            find_the_last_record.total_incme_with_last_record -= amount
            my_data = total_balance.objects.first()
            my_data.total_money_in_system += amount
            find_the_last_record.save() 
            my_data.save()
            record.delete() 
            messages.success(request, 'برداشت پول موفقانه حذف شد')
            return redirect('Finance_and_Accounting:malle_wa_mahaseba')
        else:
            record = income.objects.get(id=id)
            amount = record.income_amount
            curr = record.curr
            find_the_user = record.olabrate
            find_date_curr = record.curr
            find_the_last_record = income.objects.filter(olabrate=find_the_user,curr=find_date_curr).last()
            find_the_total_of_last = find_the_last_record.total_incme_with_last_record
            find_the_last_record.total_incme_with_last_record -= amount

            find_the_currin_currency = cuurency.objects.get(curr_name=curr)
            find_the_total_amount = find_the_currin_currency.balance
            find_the_currin_currency.balance += amount
            find_the_last_record.save()
            find_the_currin_currency.save()
            record.delete()
            messages.success(request, 'برداشت پول موفقانه حذف شد')
            return redirect('Finance_and_Accounting:malle_wa_mahaseba')
    else:
        messages.warning(request, 'نوع ریکارد نامعتبر است')
        return redirect('Finance_and_Accounting:collaborates')

import sys
import traceback


# def edit_financial_record(request, record_id):
#     record = income.objects.get(id=record_id)
#     is_income = record.is_income_or_outcome == 'دریافت'
#     original_money = record.income_amount
#     original_currency = record.curr
#     original_exchange_rate = record.exchagne_rate or 0
#     original_collaborator = record.olabrate

#     if request.method == 'POST':
#         try:
#             with transaction.atomic():
#                 if is_income:
#                     form = incomeForm(request.POST, instance=record)
#                 else:
#                     form = out_comeForm(request.POST, instance=record)
                
#                 if not form.is_valid():
#                     messages.warning(request, 'مشکل در فرم وجود دارد. لطفاً دوباره تلاش کنید.')
#                     return render(request, 'edit_financial_record.html', {
#                         'form': form,
#                         'record': record,
#                         'is_income': is_income,
#                     })
                
#                 instance = form.save(commit=False)
#                 new_collaborator = form.cleaned_data.get('olabrate')
#                 money = form.cleaned_data.get('income_amount')
#                 currency_type = form.cleaned_data.get('curr')
#                 find_the_name = currency_type.curr_name
#                 exchange_rate = form.cleaned_data.get('exchagne_rate') or 0
                
                
#                 if original_currency.curr_name == 'افغانی':
#                     my_data = total_balance.objects.select_for_update().first()
#                     if is_income:
#                         my_data.total_money_in_system -= original_money
#                     else:
#                         my_data.total_money_in_system += original_money
#                     my_data.save()
#                 else:
#                     original_curr_balance = cuurency.objects.select_for_update().get(curr_name=original_currency)
#                     if is_income:
#                         original_curr_balance.balance -= original_money
#                     else:
#                         original_curr_balance.balance += original_money
#                     original_curr_balance.save()
                
#                 # 2. Now process the new transaction with updated values
#                 if find_the_name == 'افغانی':
#                     my_data = total_balance.objects.select_for_update().first()
                    
#                     if is_income:
#                         sum = my_data.total_money_in_system + money
#                         my_data.total_money_in_system = sum
#                         my_data.save()
                        
#                     else:
#                         if money > my_data.total_money_in_system:
#                             raise ValueError('موجودی سیستم کافی نیست')
#                         mines = my_data.total_money_in_system - money
#                         my_data.total_money_in_system = mines
#                         my_data.save()
#                     instance.exchagne_rate = 0
#                     instance.exchanged_moneey = money
                    
#                 else:
#                     new_curr_balance = cuurency.objects.select_for_update().get(curr_name=currency_type)
#                     if is_income:
#                         current_balance = new_curr_balance.balance if new_curr_balance.balance is not None else 0
#                         new_curr_balance.balance = current_balance + money
#                     else:
#                         if money > new_curr_balance.balance:
#                             raise ValueError('موجودی سیستم کافی نیست')
#                         new_curr_balance.balance -= money
#                     instance.exchagne_rate = exchange_rate
#                     instance.exchanged_moneey = money * exchange_rate
#                     new_curr_balance.save()
                
#                 # 3. Update boolean field and total with last record for the NEW collaborator
#                 find_the_last_record = income.objects.filter(
#                     olabrate=new_collaborator, 
#                     curr=currency_type
#                 ).exclude(id=instance.id).order_by('-id').first()
                
#                 if find_the_last_record:
#                     find_the_last = find_the_last_record.total_incme_with_last_record
#                     new_total = instance.income_amount
                    
#                     if is_income:
#                         if new_total > find_the_last:
#                             instance.total_incme_with_last_record = new_total - find_the_last
#                             instance.blooelean_field = True
#                         elif new_total == find_the_last:
#                             instance.total_incme_with_last_record = 0
#                             instance.blooelean_field = None
#                         else:
#                             instance.total_incme_with_last_record = find_the_last - new_total
#                             instance.blooelean_field = False
#                     else:
#                         if new_total > find_the_last:
#                             instance.total_incme_with_last_record = new_total - find_the_last
#                             instance.blooelean_field = False
#                         elif new_total == find_the_last:
#                             instance.total_incme_with_last_record = 0
#                             instance.blooelean_field = None
#                         else:
#                             instance.total_incme_with_last_record = find_the_last - new_total
#                             instance.blooelean_field = True
#                 else:
#                     # No previous record for this collaborator+currency
#                     instance.total_incme_with_last_record = instance.income_amount
#                     instance.blooelean_field = True if is_income else False
                
#                 # 4. Also update the boolean field for the OLD collaborator's last record
#                 if original_collaborator != new_collaborator:
#                     old_collab_last_record = income.objects.filter(
#                         olabrate=original_collaborator,
#                         curr=original_currency
#                     ).exclude(id=instance.id).order_by('-id').first()
                    
#                     if old_collab_last_record:
#                         # Need to update the next record after the old one
#                         next_record = income.objects.filter(
#                             olabrate=original_collaborator,
#                             curr=original_currency,
#                             id__gt=old_collab_last_record.id
#                         ).order_by('id').first()
                        
#                         if next_record:
#                             next_record.total_incme_with_last_record = next_record.income_amount - old_collab_last_record.income_amount
#                             if next_record.income_amount > old_collab_last_record.income_amount:
#                                 next_record.blooelean_field = True
#                             elif next_record.income_amount == old_collab_last_record.income_amount:
#                                 next_record.blooelean_field = None
#                             else:
#                                 next_record.blooelean_field = False
#                             next_record.save()
                
#                 instance.save()
#                 messages.success(request, 'رکورد مالی موفقانه ویرایش شد')
#                 return redirect('Finance_and_Accounting:malle_wa_mahaseba')
        
#         except ValueError as e:
#             # Get the line number where error occurred
#             _, _, tb = sys.exc_info()
#             line_number = traceback.extract_tb(tb)[-1][1]
#             messages.warning(request, f'خطا در خط {line_number}: {str(e)}')
#         except Exception as e:
#             # Get full traceback information
#             exc_type, exc_value, exc_traceback = sys.exc_info()
#             tb_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
#             error_location = ''.join(tb_list[-2:])  # Get the last two lines of traceback
#             messages.error(request, f'خطای سیستمی در:\n{error_location}\n{str(e)}')
    
#     else:
#         if is_income:
#             form = incomeForm(instance=record)
#         else:
#             form = out_comeForm(instance=record)
    
#     context = {
#         'form': form,
#         'record': record,
#         'is_income': is_income,
#     }
#     return render(request, 'finanace/edit_financial_record.html', context)
def recalculate_chain(collaborator, currency):
    records = income.objects.filter(
        olabrate=collaborator,
        curr=currency
    ).order_by('id')

    last_total = 0
    last_state = None  # True = credit, False = debit, None = zero

    for record in records:
        amount = record.income_amount
        is_income = record.is_income_or_outcome == 'دریافت'

        if last_state is None:
            record.total_incme_with_last_record = amount
            record.blooelean_field = True if is_income else False

        elif last_state is True:
            if is_income:
                record.total_incme_with_last_record = last_total + amount
                record.blooelean_field = True
            else:
                if amount > last_total:
                    record.total_incme_with_last_record = amount - last_total
                    record.blooelean_field = False
                elif amount == last_total:
                    record.total_incme_with_last_record = 0
                    record.blooelean_field = None
                else:
                    record.total_incme_with_last_record = last_total - amount
                    record.blooelean_field = True

        else:  # last_state == False
            if is_income:
                if amount > last_total:
                    record.total_incme_with_last_record = amount - last_total
                    record.blooelean_field = True
                elif amount == last_total:
                    record.total_incme_with_last_record = 0
                    record.blooelean_field = None
                else:
                    record.total_incme_with_last_record = last_total - amount
                    record.blooelean_field = False
            else:
                record.total_incme_with_last_record = last_total + amount
                record.blooelean_field = False

        last_total = record.total_incme_with_last_record
        last_state = record.blooelean_field
        record.save()
def edit_financial_record(request, record_id):
    record = income.objects.get(id=record_id)
    is_income = record.is_income_or_outcome == 'دریافت'

    # Save original state
    original_amount = record.income_amount
    original_currency = record.curr
    original_collaborator = record.olabrate

    if request.method == 'POST':
        try:
            with transaction.atomic():

                form = incomeForm(request.POST, instance=record) if is_income else out_comeForm(request.POST, instance=record)

                if not form.is_valid():
                    messages.warning(request, 'فرم نادرست است')
                    return render(request, 'finanace/edit_financial_record.html', {
                        'form': form,
                        'record': record,
                        'is_income': is_income,
                    })

                instance = form.save(commit=False)
                new_amount = instance.income_amount
                new_currency = instance.curr
                new_collaborator = instance.olabrate
                exchange_rate = instance.exchagne_rate or 0

                # 🔄 1. REVERT OLD BALANCE
                if original_currency.curr_name == 'افغانی':
                    sys_balance = total_balance.objects.select_for_update().first()
                    if is_income:
                        sys_balance.total_money_in_system -= original_amount
                    else:
                        sys_balance.total_money_in_system += original_amount
                    sys_balance.save()
                else:
                    old_curr = cuurency.objects.select_for_update().get(curr_name=original_currency)
                    if is_income:
                        old_curr.balance -= original_amount
                    else:
                        old_curr.balance += original_amount
                    old_curr.save()

                # ➕ 2. APPLY NEW BALANCE
                if new_currency.curr_name == 'افغانی':
                    sys_balance = total_balance.objects.select_for_update().first()
                    if is_income:
                        sys_balance.total_money_in_system += new_amount
                    else:
                        if new_amount > sys_balance.total_money_in_system:
                            raise ValueError('موجودی کافی نیست')
                        sys_balance.total_money_in_system -= new_amount

                    instance.exchagne_rate = 0
                    instance.exchanged_moneey = new_amount
                    sys_balance.save()

                else:
                    curr_balance = cuurency.objects.select_for_update().get(curr_name=new_currency)
                    if is_income:
                        curr_balance.balance += new_amount
                    else:
                        if new_amount > curr_balance.balance:
                            raise ValueError('موجودی کافی نیست')
                        curr_balance.balance -= new_amount

                    instance.exchagne_rate = exchange_rate
                    instance.exchanged_moneey = new_amount * exchange_rate
                    curr_balance.save()

                instance.save()

                # 🔥 3. FULL RECALCULATION (THIS FIXES EVERYTHING)
                recalculate_chain(new_collaborator, new_currency)

                if original_collaborator != new_collaborator or original_currency != new_currency:
                    recalculate_chain(original_collaborator, original_currency)

                messages.success(request, 'رکورد موفقانه ویرایش شد')
                return redirect('Finance_and_Accounting:malle_wa_mahaseba')

        except ValueError as e:
            messages.warning(request, str(e))
        except Exception as e:
            messages.error(request, f'خطای سیستمی: {e}')

    else:
        form = incomeForm(instance=record) if is_income else out_comeForm(instance=record)

    return render(request, 'finanace/edit_financial_record.html', {
        'form': form,
        'record': record,
        'is_income': is_income,
    })

from django.db.models import Sum
def exchang_money(request):
    find_afghani_that_chagnes = exchagn_money_in_system.objects.filter(currency_that_you_want_tochage__curr_name='افغانی',currency_that_you_want_to_get_money__curr_name='دالر').aggregate(total_amount=Sum('currency_that_will_chage_amount'))
    total = find_afghani_that_chagnes['total_amount'] or 0

    find_dollar_that_chagnes = exchagn_money_in_system.objects.filter(currency_that_you_want_tochage__curr_name='دالر',currency_that_you_want_to_get_money__curr_name='افغانی').aggregate(total_dollar_amount=Sum('currency_that_chage_amont'))
    d_total = find_dollar_that_chagnes['total_dollar_amount'] or 0

    all_ex_records = exchagn_money_in_system.objects.all()
    my_data = total_balance.objects.first()
    all_money = my_data.total_money_in_system
    if not my_data:
        my_data = total_balance.objects.create(total_money_in_system=0)
    find_all_currency = cuurency.objects.exclude(curr_name="افغانی")
    if request.method == 'POST':
        form = exchagn_money_in_systemForm(request.POST)
        if form.is_valid():
            form_instance = form.save(commit=False)
            find_the_curency_that_want_to_change = form.cleaned_data.get('currency_that_you_want_tochage')
            find_curr_id = find_the_curency_that_want_to_change.id
            find_cuur_name = cuurency.objects.get(id=find_curr_id).curr_name
            amount_that_will_change = form.cleaned_data.get('amount')



            find_the_currency_will_bring = form.cleaned_data.get('currency_that_you_want_to_get_money')
            bring_curr_id = find_the_currency_will_bring.id
            find_bring_curr_name = cuurency.objects.get(id=bring_curr_id)
            find_b_curr_name = find_bring_curr_name.curr_name
            bring_amount = form.cleaned_data.get('want_amount')
            if find_cuur_name == 'افغانی':
                if amount_that_will_change > all_money:  
                    messages.warning(request,'پول افغانی که میخواهد تبدیل نمایید بیشتر از مجموعه پول شما در سیستم است')
                    return redirect('Finance_and_Accounting:exchang_money')
                else:
                    my_data.total_money_in_system = float(my_data.total_money_in_system) - amount_that_will_change
                    my_data.save()
                    form_instance.currency_that_will_chage_amount = amount_that_will_change
                    form_instance.currency_that_chage_amont = bring_amount
                    form_instance.save()
                    find_curr = cuurency.objects.get(id=bring_curr_id)
                    find_curr.balance = (find_curr.balance or 0) + bring_amount
                    find_curr.save()
            else:
                find_curr_balance = cuurency.objects.get(id=find_curr_id)
                if amount_that_will_change > find_curr_balance.balance:
                    messages.warning(request,f"مقدار پول { find_curr_balance.curr_name } که میخواهید تبدیل کنید بیشتر از مجموعه موجودی پول در سیستم است") 
                    return redirect('Finance_and_Accounting:exchang_money')
                else:
                    find_curr_balance.balance = find_curr_balance.balance - amount_that_will_change
                    find_curr_balance.save()
                    form_instance.currency_that_will_chage_amount = amount_that_will_change
                    form_instance.currency_that_chage_amont = bring_amount
                    form_instance.save()
                    if find_b_curr_name == 'افغانی':
                        my_data.total_money_in_system = float(my_data.total_money_in_system) + bring_amount
                        my_data.save()
                    else:
                        find_bring_curr_name.balance = find_bring_curr_name.balance + bring_amount
                        find_bring_curr_name.save()
            return redirect('Finance_and_Accounting:exchang_money')





        else:
            return HttpResponse(form.errors)
    else:
        form = exchagn_money_in_systemForm(request.POST)

    context = {
        'my_data':my_data,
        'find_all_currency':find_all_currency,
        'form':form,
        'all_ex_records':all_ex_records,
        'total':total,
        'd_total':d_total,
    }
    return render(request, 'finanace/exchange_money_from_system.html',context)
