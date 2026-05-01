from django.shortcuts import render, redirect,get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .forms import *
from django.contrib import messages
from warehouse.models import inventrories
from.models import*
from Finance_and_Accounting.models import *
from decimal import Decimal
from django.urls import reverse
# from Supplaier.models import Supplaier
from Supplaier.forms import SupplaierForm
from Customer.models import SLoan
from django.db.models import Sum
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.db.models import Sum
from django.shortcuts import get_object_or_404
import arabic_reshaper
from bidi.algorithm import get_display

def reshape_text(text):
    if not text:
        return ""
    reshaped_text = arabic_reshaper.reshape(str(text))
    return get_display(reshaped_text)

def create_both_party_purchase_ledger(customer, purchase_instance, total_amount, paid_amount, remain_amount):
    last_row = BothPartyLedger.objects.filter(customer=customer).order_by('-id').first()

    prev_supplier_balance = last_row.current_supplier_balance if last_row else Decimal('0')
    prev_customer_balance = last_row.current_customer_balance if last_row else Decimal('0')

    new_supplier_balance = prev_supplier_balance + Decimal(remain_amount)
    new_customer_balance = prev_customer_balance

    return BothPartyLedger.objects.create(
        customer=customer,
        entry_type='purchase',
        date=purchase_instance.date,
        purchase=purchase_instance,
        total_amount=Decimal(total_amount),
        paid_amount=Decimal(paid_amount),
        remain_amount=Decimal(remain_amount),
        previous_supplier_balance=prev_supplier_balance,
        previous_customer_balance=prev_customer_balance,
        current_supplier_balance=new_supplier_balance,
        current_customer_balance=new_customer_balance,
        note='ثبت خرید برای شخص هردو'
    )




def Purchase(request):  
    summary = (
        Parchase.objects.values('product__id', 'product__meat_name').annotate(
            total_quantity=Sum('quantity'),
            total_weight=Sum('wegiht')
        )
    ) 
    all_customers = Customer.objects.filter(role__in=['تامین کننده', 'هردو'])
    url = request.META.get('HTTP_REFERER') 
    my_form = ParchaseForm(request.POST or None)
    supp_form = SupplaierForm(request.POST or None)
    system_all_money = total_balance.objects.first()
    first_record = system_all_money.total_money_in_system
    find_all_sale_money = Parchase.objects.aggregate(total_should_paid=Sum('total_unit'))
    total_should_paid = find_all_sale_money['total_should_paid'] or 0
    if request.method == 'POST' and my_form.is_valid():
        try:
            with transaction.atomic():
                qauantiti = my_form.cleaned_data['quantity']
                every_price = my_form.cleaned_data['price_per_unit']
                pay = my_form.cleaned_data['paid_amount']
                customer = my_form.cleaned_data.get('supplaier')
                weightt = my_form.cleaned_data.get('wegiht')
                satatus = my_form.cleaned_data.get('status')
                
                if satatus == 'ضرب وزن':
                    totall = round(weightt * every_price)
                    remainn = totall - pay
                    if Decimal(pay) <= first_record:
                        mines = first_record - Decimal(pay)
                        system_all_money.total_money_in_system = mines
                        system_all_money.save()
                    else: 
                        messages.warning(request, 'پول موجودی در سیستم کم است لطفا پول اضافه کرده دوباره تلاش نمایید')
                        return redirect('purchase:purchase')  
                else:
                    totall = round(qauantiti * every_price) 
                    remainn = totall - pay
                    if Decimal(pay) < first_record: 
                        mines = first_record - Decimal(pay)
                        system_all_money.total_money_in_system = mines
                        system_all_money.save()
                    else: 
                        messages.warning(request, 'پول موجودی در سیستم کم است لطفا پول اضافه کرده دوباره تلاش نمایید')
                        return redirect('purchase:purchase')
                
                Purchase_instance = my_form.save(commit=False)
                Purchase_instance.remain_amount = remainn
                Purchase_instance.total_unit = totall
                if pay > totall or pay < 0 or remainn > totall or remainn < 0 :
                    messages.success(request, '  مقدار پول پرداختی یا باقی مانده شما مناسب نیست ')
                    return redirect('purchase:purchase')
                else:
                    Purchase_instance.save() 

                    LogEntry.objects.log_action( 
                        user_id=request.user.pk,
                        content_type_id=ContentType.objects.get_for_model(Purchase_instance).pk,
                        object_id=Purchase_instance.pk,
                        object_repr=force_str(Purchase_instance),
                        action_flag=ADDITION,
                        change_message=f"خرید صورت گرفت. مچموعه: {totall}, پرداخت شده : {pay}, باقی: {remainn}"
                    )

                product = Purchase_instance.product
                warehouse = Purchase_instance.warehouse
                quantity = Purchase_instance.quantity
                weights = Purchase_instance.wegiht
                new_record = inventrories.objects.create(
                    pucrchase_foerignkey=Purchase_instance,
                    product_foerignkey=product,
                    warehouse_foerignkey=warehouse,
                    Quantity=quantity,
                    weight_field=weightt,
                    in_and_out='IN'
                )
                if customer.role == 'تامین کننده':
                    if Purchase_instance.remain_amount != 0:
                        latest_unpaid_loan = SLoan.objects.filter(customer_id=customer.id).order_by('id').last()
                        if not latest_unpaid_loan:
                            latest_unpaid_loan = 0
                            find_total_amou = 0 
                        else:
                            find_total_amou = Decimal(latest_unpaid_loan.total_amount)

                        find_total = float(find_total_amou) + Purchase_instance.remain_amount
                        SLoan.objects.create(
                            customer=Purchase_instance.supplaier,  
                            sale_id=Purchase_instance,
                            amount=Purchase_instance.remain_amount,
                            total_amount=find_total,    
                            date_issued=Purchase_instance.date, 
                            due_date="",  
                            status="پرداخت نه شده",  
                            notes=""  
                        ) 
                    elif Purchase_instance.remain_amount == 0:
                        latest_unpaid_loan = SLoan.objects.filter(customer_id=customer.id).order_by('-id').first()
                        if not latest_unpaid_loan:
                            latest_unpaid_loan = 0
                            find_total_amou = 0
                        else:
                            find_total_amou = Decimal(latest_unpaid_loan.total_amount)

                        find_total = find_total_amou
                        SLoan.objects.create(
                            customer=Purchase_instance.supplaier,  
                            sale_id=Purchase_instance,
                            amount=totall,
                            total_amount=find_total,    
                            date_issued=Purchase_instance.date,  
                            due_date="", 
                            status="پرداخت شده",  
                            notes=""  
                        )
                elif customer.role == 'هردو':
                    
                    create_both_party_purchase_ledger(
                        customer=customer,
                        purchase_instance=Purchase_instance,
                        total_amount=totall,
                        paid_amount=pay,
                        remain_amount=Purchase_instance.remain_amount
                    )


                messages.success(request, 'خرید  موفقانه ثبت شد')
                return redirect('purchase:purchase')
        
        except Exception as e:
            messages.error(request, f'خطا در پردازش خرید: {str(e)}')
            return redirect('purchase:purchase')

    # Supplier form handling
    elif request.method == 'POST' and supp_form.is_valid():
        try:
            with transaction.atomic():
                is_customer = request.POST.get('type', False)
                is_customer = True if is_customer == 'on' else False
                if is_customer:
                    customer_instance = my_form.save(commit=False)
                    customer_instance.role = 'هردو'
                else:
                    customer_instance = my_form.save(commit=False)
                    customer_instance.role = 'تامین کننده' 
                supp_form.save()
                messages.success(request, ' تامین کننده موفقانه ثبت شد')
                return HttpResponseRedirect(url)
        
        except Exception as e:
            messages.error(request, f'خطا در ثبت تامین کننده: {str(e)}')
            return redirect('purchase:purchase')
        
    else:
        my_data = Parchase.objects.all()

        my_form = ParchaseForm()
        supp_form = SupplaierForm()
        context = {
            'my_form':my_form,
            'my_data':my_data,
            'supp_form':supp_form,
            'total_should_paid':total_should_paid,
            'all_customers':all_customers,
            'summary':summary,
        }

    return render(request, 'purchase/purchase_page.html', context)









def reciving_item(request,id):
    customer = get_object_or_404(Customer, id=id)
    my_form = item_dealsForms(request.POST or None)
    if request.method == 'POST' and my_form.is_valid():
        customer_instance = my_form.save(commit=False)
        find_the_product = customer_instance.item
        warehouse_for = customer_instance.godam
        num = customer_instance.number
        wegit = customer_instance.weighht
        customer_instance.dealer = customer
        customer_instance.status = 'رسید'
        customer_instance.save()
        new_record  = inventrories.objects.create(product_foerignkey=find_the_product,warehouse_foerignkey=warehouse_for,Quantity=num,weight_field=wegit,in_and_out='IN')
        messages.success(request, ' جنس با موفقیت رسید شد')
        return redirect('purchase:purhase_with_item', id=id)


    else:
        my_form = item_dealsForms()
    context = {
        'my_form':my_form,
    }
    return render(request,'purchase/recirdving_item.html',context)



def giving_item(request,id):
    customer = get_object_or_404(Customer, id=id)
    my_form = item_dealsForms(request.POST or None)
    if request.method == 'POST' and my_form.is_valid():
        customer_instance = my_form.save(commit=False)
        find_the_product = customer_instance.item
        warehouse_for = customer_instance.godam
        num = customer_instance.number
        wegit = customer_instance.weighht
        customer_instance.dealer = customer
        customer_instance.status = 'برداشت'
        customer_instance.save()
        new_record  = inventrories.objects.create(product_foerignkey=find_the_product,warehouse_foerignkey=warehouse_for,Quantity=num,weight_field=wegit,in_and_out='OUT')
        messages.success(request, ' جنس با موفقیت برداشت شد')
        return redirect('purchase:purhase_with_item', id=id)
    else:
        my_form = item_dealsForms()
    context = {
        'my_form':my_form,
    }
    return render(request,'purchase/giving_item.html',context)








import random

def random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)


def purhase_with_item(request,id):
    customer = get_object_or_404(Customer, id=id)
    deals = item_deals.objects.filter(dealer=id)
    product_ids = deals.values_list('item', flat=True).distinct()

    product_summaries = []
    msg=None

    for pid in product_ids:
        product_obj = product.objects.get(id=pid)
        product_name = product_obj.meat_name  

        recv = deals.filter(item=pid, status='رسید')
        give = deals.filter(item=pid, status='برداشت')

        total_recv_num = recv.aggregate(total=Sum('number'))['total'] or 0
        total_recv_weight = recv.aggregate(total=Sum('weighht'))['total'] or 0

        total_give_num = give.aggregate(total=Sum('number'))['total'] or 0
        total_give_weight = give.aggregate(total=Sum('weighht'))['total'] or 0
        text_color = random_color()
        
        if total_recv_weight > total_give_weight:
            difference = total_recv_weight - total_give_weight
            msg_text = f"{product_name}: شما باید {difference} کیلوگرام به این شخص بدهید."
            msg_text_color = "green" 
        else:
            difference = total_give_weight - total_recv_weight
            msg_text = f"{product_name}: شما باید {difference} کیلوگرام از این شخص بگیرید."
            msg_text_color = "red"

        msg = f"""
        <div style="
            border: 2px solid {text_color};
            color: {msg_text_color};
            font-weight:bold;
            padding: 10px 15px;
            border-radius: 8px;
            margin: 5px 0;
            text-align:center;
            background:#f9f9f9;
            ">
            {msg_text}
        </div>
        """

        product_summaries.append({
            "product": product_name,
            "recv_num": total_recv_num,
            "recv_weight": total_recv_weight,
            "give_num": total_give_num,
            "give_weight": total_give_weight,
            "difference": difference,
            "message": msg,
        })

    context = {
        'customer':customer,
        'deals':deals,
        'message':msg,
        'product_summaries':product_summaries,
    }
    return render(request,'purchase/purchase_with_item.html',context)

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.contrib.staticfiles.storage import staticfiles_storage 

def purchase_with_item_pdf(request, id):
    customer = get_object_or_404(Customer, id=id)
    deals = item_deals.objects.filter(dealer=id)

    # Register a Persian font
    font_path = staticfiles_storage.path('fonts/Amiri-Regular.ttf')  # make sure the font exists
    pdfmetrics.registerFont(TTFont('Amiri', font_path))
    font_name = 'Amiri'

    # Prepare data
    reshaped_deals = []
    for i in deals:
        reshaped_deals.append([
            reshape_text(i.notes),
            str(i.weighht),
            str(i.number),
            reshape_text(i.item),
            reshape_text(i.date_day),
            str(i.id),
        ])

    headers = [
        reshape_text("توضیحات"),
        reshape_text("وزن"),
        reshape_text("تعداد"),
        reshape_text("محصول"),
        reshape_text("تاریخ"),
        reshape_text("شماره"),
    ]
    data = [headers] + reshaped_deals

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="purchase_{id}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    persian_style = ParagraphStyle(
        name='PersianStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        alignment=1,  # center
    )

    elements = []

    # Title
    elements.append(Paragraph(reshape_text(customer.name), persian_style))
    elements.append(Spacer(1, 20))

    # Table
    table = Table(data, colWidths=[40, 80, 100, 50, 50, 150])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ]))

    elements.append(table)
    doc.build(elements)

    return response













@login_required
def log_in_our_system(request):
    logs = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')
    return render(request, 'purchase/all_logs.html', {'logs': logs})

def delete_Purchase(request, id):
    try:
        with transaction.atomic():
            purchase = get_object_or_404(Parchase, id=id)
            customer_obj = purchase.supplaier
            system_all_money = total_balance.objects.first()
            
            if system_all_money:
                system_all_money.total_money_in_system += Decimal(purchase.paid_amount or 0)
                system_all_money.save()

            # =========================
            # old supplier logic kept
            # new both-party logic added
            # =========================
            if customer_obj.role == 'تامین کننده':
                related_loans = SLoan.objects.filter(sale_id=purchase).first()

                if related_loans:
                    find_the_remain_amount = Decimal(related_loans.sale_id.remain_amount or 0)
                    find_the_customer_id = related_loans.sale_id.supplaier_id

                    if related_loans.status == "پرداخت نه شده":
                        find_the_sloan_for_supp = SLoan.objects.filter(customer_id=find_the_customer_id).last()
                        if find_the_sloan_for_supp:
                            mines_from_total_remian = Decimal(find_the_sloan_for_supp.total_amount or 0) - find_the_remain_amount
                            related_loans.delete()
                            find_the_sloan_for_supp.total_amount = mines_from_total_remian
                            find_the_sloan_for_supp.save()
                        else:
                            related_loans.delete()
                    else:
                        related_loans.delete()

            elif customer_obj.role == 'هردو':
                BothPartyLedger.objects.filter(
                    customer=customer_obj,
                    purchase=purchase,
                    entry_type='purchase'
                ).delete()

            inventrories.objects.filter(
                pucrchase_foerignkey=purchase.id,
                product_foerignkey=purchase.product,
                warehouse_foerignkey=purchase.warehouse,
                Quantity=purchase.quantity,
                weight_field=purchase.wegiht
            ).delete()

            purchase.delete()

            # recalculate ledger only for both-person
            if customer_obj.role == 'هردو':
                recalculate_both_party_ledger(customer_obj)

            messages.success(request, 'خرید موفقانه حذف شد')
            return redirect('purchase:purchase')
    
    except Exception as e:
        messages.error(request, f'خطا در حذف خرید: {str(e)}')
        return redirect('purchase:purchase')





def loan(request):
    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        record = get_object_or_404(Parchase, id=record_id)
        loan_amount = record.remain_amount
        paid_amou = record.paid_amount

        my_form = Purchase_loanForm(request.POST)
        if my_form.is_valid():
            second_pay = my_form.cleaned_data['pay_amount']
            if second_pay <= loan_amount and second_pay > 0:
                mines_from_total_loan = loan_amount - second_pay
                sum_of_this_paid_amount = paid_amou + second_pay
                record.paid_amount = sum_of_this_paid_amount
                record.remain_amount = mines_from_total_loan
                record.save()
                record.save()
            else:
                messages.warning(request,'مشکل موجود است')
                return redirect('purchase:loan')
            my_form.save()
            messages.success(request, 'باقی قرض موفقانه اجرا شد ')
            return redirect('purchase:loan')
        else:
            messages.warning(request,'مشکل موجود است')
            return redirect('purchase:loan')
    else:
        records = Parchase.objects.filter(remain_amount__gt=0)
        my_form = Purchase_loanForm()

    context = { 
        'records':records, 
        'my_form':my_form,
    }
    return render(request, 'purchase/loans.html',context)
    
    

def recalculate_both_party_ledger(customer):
    rows = BothPartyLedger.objects.filter(customer=customer).order_by('id')

    supplier_balance = Decimal('0')
    customer_balance = Decimal('0')

    for row in rows:
        row.previous_supplier_balance = supplier_balance
        row.previous_customer_balance = customer_balance

        if row.entry_type == 'purchase':
            supplier_balance += Decimal(row.remain_amount or 0)

        elif row.entry_type == 'sale':
            customer_balance += Decimal(row.remain_amount or 0)

        elif row.entry_type == 'pay_to_partner':
            amount = Decimal(row.total_amount or 0)
            supplier_balance -= amount

        elif row.entry_type == 'receive_from_partner':
            amount = Decimal(row.total_amount or 0)
            customer_balance -= amount

        row.current_supplier_balance = supplier_balance
        row.current_customer_balance = customer_balance

        row.save(update_fields=[
            'previous_supplier_balance',
            'previous_customer_balance',
            'current_supplier_balance',
            'current_customer_balance',
        ])



# def edit_purchase(request, purchase_id):
#     purchase = get_object_or_404(Parchase, id=purchase_id)
#     system_all_money = total_balance.objects.first()
#     first_record = system_all_money.total_money_in_system if system_all_money else Decimal('0')

#     original_total = purchase.total_unit
#     original_paid = purchase.paid_amount
#     original_remain = purchase.remain_amount
#     original_status = purchase.status
#     orginal_product = purchase.product
#     original_suppliar = purchase.supplaier
#     original_warehouse = purchase.warehouse
    
#     old_both_customer = None
#     if request.method == 'POST':
#         form = ParchaseForm(request.POST, instance=purchase)
#         if form.is_valid():
#             try:
#                 with transaction.atomic():
#                     inventory_entry = inventrories.objects.get(product_foerignkey=orginal_product,pucrchase_foerignkey=purchase,warehouse_foerignkey=original_warehouse)
#                     inventory_entry.delete()
#                     if original_suppliar.role == 'تامین کننده':
#                         loan_entry = SLoan.objects.filter(
#                             customer=original_suppliar,
#                             sale_id=purchase
#                         ).first()

#                         later_loans = SLoan.objects.filter(customer=original_suppliar).last()
#                         if later_loans:
#                             mines_amount = Decimal(later_loans.total_amount or 0) - Decimal(original_remain or 0)
#                             later_loans.total_amount = mines_amount
#                             later_loans.save()

#                         if loan_entry:
#                             loan_entry.delete()

#                     elif original_suppliar.role == 'هردو':
#                         old_both_customer = original_suppliar
#                         BothPartyLedger.objects.filter(
#                             customer=original_suppliar,
#                             purchase=purchase,
#                             entry_type='purchase'
#                         ).delete()
                    
                    
#                     # Delete or update loan entry
#                     # loan_entry = SLoan.objects.get(customer=original_suppliar,sale_id=purchase)
#                     # later_loans = SLoan.objects.filter(customer=original_suppliar).last()
#                     # mines_amount = later_loans.total_amount - original_remain
#                     # later_loans.total_amount = mines_amount
#                     # later_loans.save()
#                     # loan_entry.delete()
                    
#                     # Now apply the new changes (similar to your original logic)
#                     quantity = form.cleaned_data['quantity']
#                     price_per_unit = form.cleaned_data['price_per_unit']
#                     paid_amount = form.cleaned_data['paid_amount']
                    
#                     customer = form.cleaned_data.get('supplaier')
#                     weight = form.cleaned_data.get('wegiht')
#                     status = form.cleaned_data.get('status')
                    
#                     if status == 'ضرب وزن':
#                         total = round(weight * price_per_unit)
#                         remain = total - paid_amount
#                         if Decimal(paid_amount) <= first_record:
#                             mines = first_record + Decimal(original_paid) - Decimal(paid_amount)
#                             system_all_money.total_money_in_system = mines
#                             system_all_money.save()
#                         else: 
#                             messages.warning(request, 'پول موجودی در سیستم کم است لطفا پول اضافه کرده دوباره تلاش نمایید')
#                             return redirect('purchase:purchase')  
#                     else:
#                         total = round(quantity * price_per_unit) 
#                         remain = total - paid_amount
#                         if Decimal(total) < first_record: 
#                             mines = first_record + Decimal(original_paid) - Decimal(paid_amount)
#                             system_all_money.total_money_in_system = mines
#                             system_all_money.save()
#                         else: 
#                             messages.warning(request, 'پول موجودی در سیستم کم است لطفا پول اضافه کرده دوباره تلاش نمایید')
#                             return redirect('purchase:purchase')
                    
#                     # Update purchase instance
#                     purchase_instance = form.save(commit=False)
#                     purchase_instance.remain_amount = remain
#                     purchase_instance.total_unit = total
                    
#                     if paid_amount > total or paid_amount < 0 or remain > total or remain < 0:
#                         messages.success(request, 'مقدار پول پرداختی یا باقی مانده شما مناسب نیست')
#                         return redirect('purchase:purchase')
#                     else:
#                         purchase_instance.save() 

                        

#                     # Create new inventory entry
#                     product = purchase_instance.product
#                     warehouse = purchase_instance.warehouse
#                     inventrories.objects.create(
#                         pucrchase_foerignkey=purchase_instance,
#                         product_foerignkey=product,
#                         warehouse_foerignkey=warehouse,
#                         Quantity=quantity,
#                         weight_field=weight,
#                         in_and_out='IN'
#                     )

#                     # Handle loan creation
#                     if customer.role == 'تامین کننده':
#                         if purchase_instance.remain_amount != 0:
#                             latest_unpaid_loan = SLoan.objects.filter(customer_id=customer.id).order_by('id').last()
#                             if not latest_unpaid_loan:
#                                 latest_unpaid_loan = 0
#                                 find_total_amou = 0
#                             else:
#                                 find_total_amou = Decimal(latest_unpaid_loan.total_amount)

#                             find_total = float(find_total_amou) + purchase_instance.remain_amount
#                             SLoan.objects.create(
#                                 customer=purchase_instance.supplaier,  
#                                 sale_id=purchase_instance,
#                                 amount=purchase_instance.remain_amount,
#                                 total_amount=find_total,    
#                                 date_issued=purchase_instance.date, 
#                                 due_date="",  
#                                 status="پرداخت نه شده",  
#                                 notes=""  
#                             ) 
#                         elif purchase_instance.remain_amount == 0:
#                             latest_unpaid_loan = SLoan.objects.filter(customer_id=customer.id).order_by('-id').first()
#                             if not latest_unpaid_loan:
#                                 latest_unpaid_loan = 0
#                                 find_total_amou = 0
#                             else:
#                                 find_total_amou = Decimal(latest_unpaid_loan.total_amount)

#                             find_total = find_total_amou
#                             SLoan.objects.create(
#                                 customer=purchase_instance.supplaier,  
#                                 sale_id=purchase_instance,
#                                 amount=total,
#                                 total_amount=find_total,    
#                                 date_issued=purchase_instance.date,  
#                                 due_date="", 
#                                 status="پرداخت شده",  
#                                 notes=""  
#                             )
#                     elif customer.role == 'هردو':
#                         BothPartyLedger.objects.create(
#                             customer=customer,
#                             entry_type='purchase',
#                             date=purchase_instance.date,
#                             purchase=purchase_instance,
#                             total_amount=Decimal(total),
#                             paid_amount=Decimal(paid_amount),
#                             remain_amount=Decimal(purchase_instance.remain_amount),
#                             previous_supplier_balance=Decimal('0'),
#                             previous_customer_balance=Decimal('0'),
#                             current_supplier_balance=Decimal('0'),
#                             current_customer_balance=Decimal('0'),
#                             note='ویرایش خرید برای شخص هردو'
#                         )
#                     if old_both_customer:
#                         recalculate_both_party_ledger(old_both_customer)

#                     if customer.role == 'هردو':
#                         recalculate_both_party_ledger(customer)

#                     messages.success(request, 'خرید موفقانه ویرایش شد')
#                     return redirect('purchase:purchase')
#             except Exception as e:
#                 messages.error(request, f'خطایی رخ داده است: {str(e)}')
#                 return redirect('purchase:purchase')
            
            
#     else:
#         form = ParchaseForm(instance=purchase)
    
#     context = {
#         'form': form,
#         'purchase': purchase,
#     }

#     return render(request, 'purchase/edit_purchase.html', context)


def edit_purchase(request, purchase_id):
    purchase = get_object_or_404(Parchase, id=purchase_id)
    system_all_money = total_balance.objects.first()

    if not system_all_money:
        messages.warning(request, 'رکورد صندوق سیستم موجود نیست')
        return redirect('purchase:purchase')

    original_total = Decimal(purchase.total_unit or 0)
    original_paid = Decimal(purchase.paid_amount or 0)
    original_remain = Decimal(purchase.remain_amount or 0)
    original_status = purchase.status
    orginal_product = purchase.product
    original_suppliar = purchase.supplaier
    original_warehouse = purchase.warehouse

    old_both_customer = None

    if request.method == 'POST':
        form = ParchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            try:
                with transaction.atomic():
                    inventory_entry = inventrories.objects.filter(
                        product_foerignkey=orginal_product,
                        pucrchase_foerignkey=purchase,
                        warehouse_foerignkey=original_warehouse
                    ).first()
                    if inventory_entry:
                        inventory_entry.delete()

                    if original_suppliar.role == 'تامین کننده':
                        loan_entry = SLoan.objects.filter(
                            customer=original_suppliar,
                            sale_id=purchase
                        ).first()

                        later_loans = SLoan.objects.filter(customer=original_suppliar).last()
                        if later_loans:
                            mines_amount = Decimal(later_loans.total_amount or 0) - Decimal(original_remain or 0)
                            later_loans.total_amount = mines_amount
                            later_loans.save()

                        if loan_entry:
                            loan_entry.delete()

                    elif original_suppliar.role == 'هردو':
                        old_both_customer = original_suppliar
                        BothPartyLedger.objects.filter(
                            customer=original_suppliar,
                            purchase=purchase,
                            entry_type='purchase'
                        ).delete()

                    quantity = Decimal(form.cleaned_data['quantity'] or 0)
                    price_per_unit = Decimal(form.cleaned_data['price_per_unit'] or 0)
                    paid_amount = Decimal(form.cleaned_data['paid_amount'] or 0)
                    customer = form.cleaned_data.get('supplaier')
                    weight = Decimal(form.cleaned_data.get('wegiht') or 0)
                    status = form.cleaned_data.get('status')

                    # محاسبه total و remain
                    if status == 'ضرب وزن':
                        total = Decimal(round(weight * price_per_unit))
                    else:
                        total = Decimal(round(quantity * price_per_unit))

                    remain = total - paid_amount

                    # validation
                    if paid_amount > total or paid_amount < 0 or remain > total or remain < 0:
                        messages.warning(request, 'مقدار پول پرداختی یا باقی مانده شما مناسب نیست')
                        return redirect('purchase:purchase')

                    # -------------------------------
                    # منطق درست صندوق در ویرایش
                    # -------------------------------
                    current_system_money = Decimal(system_all_money.total_money_in_system or 0)

                    # اول پول قبلی را دوباره به صندوق برگردان
                    available_money = current_system_money + original_paid

                    # حالا پول جدید را از صندوق کم کن
                    if paid_amount <= available_money:
                        system_all_money.total_money_in_system = available_money - paid_amount
                        system_all_money.save()
                    else:
                        messages.warning(request, 'پول موجودی در سیستم کم است لطفا پول اضافه کرده دوباره تلاش نمایید')
                        return redirect('purchase:purchase')

                    # ذخیره خرید
                    purchase_instance = form.save(commit=False)
                    purchase_instance.remain_amount = remain
                    purchase_instance.total_unit = total
                    purchase_instance.save()

                    # ایجاد دوباره موجودی انبار
                    inventrories.objects.create(
                        pucrchase_foerignkey=purchase_instance,
                        product_foerignkey=purchase_instance.product,
                        warehouse_foerignkey=purchase_instance.warehouse,
                        Quantity=quantity,
                        weight_field=weight,
                        in_and_out='IN'
                    )

                    # Handle loan creation
                    if customer.role == 'تامین کننده':
                        if purchase_instance.remain_amount != 0:
                            latest_unpaid_loan = SLoan.objects.filter(customer_id=customer.id).order_by('id').last()
                            if not latest_unpaid_loan:
                                find_total_amou = Decimal('0')
                            else:
                                find_total_amou = Decimal(latest_unpaid_loan.total_amount or 0)

                            find_total = find_total_amou + Decimal(purchase_instance.remain_amount)
                            SLoan.objects.create(
                                customer=purchase_instance.supplaier,
                                sale_id=purchase_instance,
                                amount=purchase_instance.remain_amount,
                                total_amount=find_total,
                                date_issued=purchase_instance.date,
                                due_date="",
                                status="پرداخت نه شده",
                                notes=""
                            )
                        else:
                            latest_unpaid_loan = SLoan.objects.filter(customer_id=customer.id).order_by('-id').first()
                            if not latest_unpaid_loan:
                                find_total_amou = Decimal('0')
                            else:
                                find_total_amou = Decimal(latest_unpaid_loan.total_amount or 0)

                            SLoan.objects.create(
                                customer=purchase_instance.supplaier,
                                sale_id=purchase_instance,
                                amount=total,
                                total_amount=find_total_amou,
                                date_issued=purchase_instance.date,
                                due_date="",
                                status="پرداخت شده",
                                notes=""
                            )

                    elif customer.role == 'هردو':
                        BothPartyLedger.objects.create(
                            customer=customer,
                            entry_type='purchase',
                            date=purchase_instance.date,
                            purchase=purchase_instance,
                            total_amount=Decimal(total),
                            paid_amount=Decimal(paid_amount),
                            remain_amount=Decimal(purchase_instance.remain_amount),
                            previous_supplier_balance=Decimal('0'),
                            previous_customer_balance=Decimal('0'),
                            current_supplier_balance=Decimal('0'),
                            current_customer_balance=Decimal('0'),
                            note='ویرایش خرید برای شخص هردو'
                        )

                    if old_both_customer:
                        recalculate_both_party_ledger(old_both_customer)

                    if customer.role == 'هردو':
                        recalculate_both_party_ledger(customer)

                    messages.success(request, 'خرید موفقانه ویرایش شد')
                    return redirect('purchase:purchase')

            except Exception as e:
                messages.error(request, f'خطایی رخ داده است: {str(e)}')
                return redirect('purchase:purchase')
    else:
        form = ParchaseForm(instance=purchase)

    context = {
        'form': form,
        'purchase': purchase,
    }
    return render(request, 'purchase/edit_purchase.html', context)

from warehouse.models import warehouse_info
def delete_item_deal(request,id):
    referer = request.META.get('HTTP_REFERER', '/') 
    find_record = item_deals.objects.get(id=id)
    find_quantity = find_record.number
    find_eight = find_record.weighht
    find_produt = find_record.item.id
    find_pro = product.objects.get(id=find_produt)
    ware_ids = find_record.godam.id
    ware_id = warehouse_info.objects.get(id=ware_ids)
    if find_record.status == 'رسید':
        
        new_record = inventrories.objects.create(product_foerignkey=find_pro,warehouse_foerignkey=ware_id,Quantity=find_quantity,weight_field=find_eight,in_and_out='OUT')
        find_record.delete()
        messages.success(request, f'ریکارد رسید موفقانه حذف شد')
        return redirect(referer)
    else:
        new_record = inventrories.objects.create(product_foerignkey=find_pro,warehouse_foerignkey=ware_id,Quantity=find_quantity,weight_field=find_eight,in_and_out='IN')
        find_record.delete()
        messages.success(request, f'ریکارد برداشت موفقانه حذف شد')
        return redirect(referer)


        
        
