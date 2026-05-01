from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import *
from .models import Order,Order_Item,Sale,Return,Return_Details,order_loan,sale_item_part
from django.db import transaction
from purchase.models import *
from django.db.models import Sum
from django.urls import reverse
from decimal import Decimal
from Finance_and_Accounting.models import total_balance
from django.db import transaction
from Customer.models import Loan
from Customer.forms import CustomerForm
from Order.models import Sale
from warehouse.models import inventrories,warehouse_info

from django.forms import modelform_factory, inlineformset_factory

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from django.contrib.staticfiles.storage import staticfiles_storage
import arabic_reshaper
from bidi.algorithm import get_display

# Create your views here.


def order(request):
    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        order_item_form = Order_ItemForm(request.POST)

        if order_form.is_valid():  # Validate the Order form first
            # Save the Order instance
            order = order_form.save()

            order_item_data = request.POST.copy()
            order_item_data['order'] = order.id
            order_item_form = Order_ItemForm(order_item_data)

            if order_item_form.is_valid():
                # Save the Order_Item instance
                order_item = order_item_form.save()

                if order.status == 'complete':
                    order_items = Order_Item.objects.filter(order=order)
                    for item in order_items:
                        # Calculate and save total amount
                        item.total_amount = item.quantity * item.price_per_unit
                        item.save()

                        # Adjust stock in Purchase
                        try:
                            Purchase = Parchase.objects.get(product=item.product)
                            if Purchase.quantity >= item.quantity:
                                Purchase.quantity -= item.quantity
                                Purchase.save()
                            else:
                                messages.error(request, f"موجودی کافی برای {item.product} وجود ندارد.")
                                order.delete()  # Rollback the order
                                return redirect('Order:order')
                        except Parchase.DoesNotExist:
                            messages.error(request, f"رکورد خریدی برای {item.product} یافت نشد.")
                            order.delete()  # Rollback the order
                            return redirect('Order:order')

                # Redirect or success message
                messages.success(request, "سفارش و اقلام سفارش با موفقیت ذخیره شدند.")
                return redirect('Order:order')
            else:
                # Delete the saved Order if Order_Item fails
                order.delete()
                messages.error(request, f"خطا در فرم اقلام سفارش: {order_item_form.errors}")
        else:
            messages.error(request, f"خطا در فرم سفارش: {order_form.errors}")
    else:
        # For GET requests, instantiate empty forms
        order_form = OrderForm()
        order_item_form = Order_ItemForm()
        all_order = Order.objects.order_by('customer').distinct('customer')
        all_order_item = Order_Item.objects.all()

    context = {
        'order_form': order_form,
        'order_item_form': order_item_form,
        'all_order': all_order,
        'all_order_item': all_order_item
    }
    return render(request, 'Order/order.html', context)

def delete_order(request, id):
    # Fetch the Order instance or return a 404 error
    order_instance = get_object_or_404(Order, pk=id)

    # Fetch all related Order_Item instances and delete them
    order_items = Order_Item.objects.filter(order=order_instance)
    order_items.delete()

    # Delete the order instance
    order_instance.delete()

    # Add a success message
    messages.success(request, 'مشتری شما موفقانه حذف شد ')

    # Redirect to the main order page
    return redirect('Order:order')

def edit_order(request, id):
    # Fetch the Order object and its associated Order_Item object
    order_instance = get_object_or_404(Order, pk=id)
    order_item_instance = get_object_or_404(Order_Item, order=order_instance)  # Assuming a ForeignKey relation

    if request.method == "POST":
        # Process the forms for Order and Order_Item separately
        order_form = OrderForm(request.POST, instance=order_instance)
        order_item_form = Order_ItemForm(request.POST, instance=order_item_instance)

        if order_form.is_valid() and order_item_form.is_valid():
            # Save both forms
            order_form.save()
            order_item_form.save()

            # Success message
            messages.success(request, 'تغییرات در مشتری ذیل موفقانه انجام پذیرفت')
            return HttpResponseRedirect(reverse("Order:order"))  # Redirect to order listing page
    else:
        # If GET request, create forms with existing data
        order_form = OrderForm(instance=order_instance)
        order_item_form = Order_ItemForm(instance=order_item_instance)

        context = {
            'edit_daily_project_form': order_form,
            'edit_daily_project_forms': order_item_form,
            'id': id,
        }
        return render(request, "Order/edit_order.html", context)

from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404
def create_both_party_sale_ledger(customer, sale_instance, sale_item, total_amount, paid_amount, remain_amount):
    last_row = BothPartyLedger.objects.filter(customer=customer).order_by('-id').first()

    prev_supplier_balance = last_row.current_supplier_balance if last_row else Decimal('0')
    prev_customer_balance = last_row.current_customer_balance if last_row else Decimal('0')

    new_supplier_balance = prev_supplier_balance
    new_customer_balance = prev_customer_balance + Decimal(remain_amount)

    return BothPartyLedger.objects.create(
        customer=customer,
        entry_type='sale',
        date=sale_instance.reg_date,
        sale=sale_item,
        total_amount=Decimal(total_amount),
        paid_amount=Decimal(paid_amount),
        remain_amount=Decimal(remain_amount),
        previous_supplier_balance=prev_supplier_balance,
        previous_customer_balance=prev_customer_balance,
        current_supplier_balance=new_supplier_balance,
        current_customer_balance=new_customer_balance,
        note='ثبت فروش برای شخص هردو'
    )

# def Direct_sale(request):
#     summary = (
#         sale_item_part.objects.values('product__id', 'product__meat_name').annotate(
#             total_quantity=Sum('quantity'),
#             total_weight=Sum('weight')
#         )
#     )
#     SaleItemFormSet = modelformset_factory(sale_item_part, form=sale_itemForm, extra=0, can_delete=True)
#     sale_item_formset = SaleItemFormSet(request.POST or None, queryset=sale_item_part.objects.none())
#     find_all_sale_money = sale_item_part.objects.aggregate(total_should_paid=Sum('should_paid'))
#     total_should_paid = find_all_sale_money['total_should_paid'] or 0
#     customer_list =  Customer.objects.filter(role__in=['مشتری', 'هردو'])
    
#     my_form = SaleForm(request.POST or None)
#     products = product.objects.all()
#     warehouses = warehouse_info.objects.all()
#     my_date = sale_item_part.objects.all().order_by('id')
#     system_all_money = total_balance.objects.first()
#     try:
#         first_record = system_all_money.total_money_in_system
#     except:
#         return HttpResponse('پول در سیستم موجود نیست ..!')

#     if request.method == 'POST':
#         if my_form.is_valid() and sale_item_formset.is_valid():
            
#             try:
#                 with transaction.atomic():  
#                     customer = my_form.cleaned_data.get('customer')
#                     sale_ins = my_form.save(commit=False)
#                     sale_instance = my_form.save()
                    
#                     sale_items = sale_item_formset.save(commit=False)

#                     for form, sale_item in zip(sale_item_formset.forms, sale_items):
#                         if form.cleaned_data:
#                             quantity = form.cleaned_data.get('quantity')
#                             weight = form.cleaned_data.get('weight')
#                             price_per_unit = form.cleaned_data.get('price_per_unit')
#                             paid_amount_for_every_record = form.cleaned_data.get('paid_amount_for_every_record')
#                             product_instance = form.cleaned_data.get('product')
#                             warehouse_instance = form.cleaned_data.get('warehouse')
#                             status = form.cleaned_data.get('status')
                            

#                             # Lock relevant inventory rows
#                             all_data = inventrories.objects.select_for_update().filter(
#                                 warehouse_foerignkey=warehouse_instance,
#                                 product_foerignkey=product_instance
#                             )

#                             find_purchase_date = inventrories.objects.filter(
#                                 warehouse_foerignkey=warehouse_instance,
#                                 product_foerignkey=product_instance,
#                                 in_and_out='IN'
#                             ).values(
#                                 'product_foerignkey', 'product_foerignkey__meat_name'
#                             ).annotate(
#                                 total_weight_in_purchase=Sum('weight_field'),
#                                 total_quantity_in_purchase=Sum('Quantity')
#                             )

#                             find_sell_date = inventrories.objects.filter(
#                                 warehouse_foerignkey=warehouse_instance,
#                                 product_foerignkey=product_instance,
#                                 in_and_out='OUT'
#                             ).values(
#                                 'product_foerignkey', 'product_foerignkey__meat_name'
#                             ).annotate(
#                                 total_weight_in_sell=Sum('weight_field'),
#                                 total_quantity_in_sell=Sum('Quantity')
#                             )

#                             sell_data_dict = {item['product_foerignkey']: item for item in find_sell_date}
#                             for purchase in find_purchase_date:
#                                 product_id = purchase['product_foerignkey']
#                                 product_name = purchase['product_foerignkey__meat_name']
#                                 total_weight_in = purchase['total_weight_in_purchase'] or 0
#                                 total_quantity_in = purchase['total_quantity_in_purchase'] or 0

#                                 total_weight_out = sell_data_dict.get(product_id, {}).get('total_weight_in_sell', 0)
#                                 total_quantity_out = sell_data_dict.get(product_id, {}).get('total_quantity_in_sell', 0)

#                                 weight_difference = total_weight_in - total_weight_out
#                                 quantity_difference = total_quantity_in - total_quantity_out

#                                 if weight <= weight_difference and quantity <= quantity_difference:
#                                     if status == 'ضرب وزن':
#                                         should_paid = round(weight * price_per_unit)
#                                     else:
#                                         should_paid = round(quantity * price_per_unit)

#                                     borrow_amount = should_paid - paid_amount_for_every_record

#                                     sale_item.should_paid = should_paid
#                                     sale_item.borrow_amount = borrow_amount
#                                     sale_item.sell_forei = sale_instance
#                                     sale_item.reamin_amount_according_to_sale_record = borrow_amount

#                                     if Decimal(should_paid) > 0:
#                                         system_all_money = total_balance.objects.select_for_update().first()
#                                         system_all_money.total_money_in_system += Decimal(paid_amount_for_every_record)
#                                         system_all_money.save()

#                                         messages.success(request, 'مقدار شما قابل فروش است تشکر ...!')
#                                     else:
#                                         raise ValueError('پول مجموعی جنس کم است')

#                                     sale_item.save()

#                                     inventrories.objects.create(
#                                         product_foerignkey=product_instance,
#                                         warehouse_foerignkey=warehouse_instance,
#                                         sale_forignkey=sale_item,
#                                         Quantity=quantity,
#                                         weight_field=weight,
#                                         in_and_out='OUT'
#                                     )
#                                     if customer.role == 'مشتری':
#                                         if sale_item.borrow_amount != 0:
#                                             latest_unpaid_loan = Loan.objects.filter(customer_id=customer.id).order_by('-id').first()
#                                             find_total_amount = Decimal(latest_unpaid_loan.total_amount) if latest_unpaid_loan else 0
#                                             total_amount = float(find_total_amount) + sale_item.borrow_amount
#                                             Loan.objects.create(
#                                                 customer=my_form.instance.customer,
#                                                 sale_id=sale_item,
#                                                 amount=sale_item.borrow_amount,
#                                                 total_amount=total_amount,
#                                                 date_issued=my_form.instance.reg_date,
#                                                 due_date="",
#                                                 status="پرداخت نه شده",
#                                                 notes=""
#                                             ) 
#                                         elif sale_item.borrow_amount == 0:
#                                             latest_unpaid_loan = Loan.objects.filter(customer_id=customer.id).order_by('-id').first()
#                                             find_total_amount = Decimal(latest_unpaid_loan.total_amount) if latest_unpaid_loan else 0
#                                             total_amount = find_total_amount
#                                             find_the_new_Saved_erord = sale_item_part.objects.last()
#                                             find_the_new_Saved_erord.is_money_approved = True
#                                             find_the_new_Saved_erord.save()


#                                             Loan.objects.create(
#                                                 customer=my_form.instance.customer,
#                                                 sale_id=sale_item,
#                                                 amount=should_paid,
#                                                 total_amount=total_amount,
#                                                 date_issued=my_form.instance.reg_date,
#                                                 due_date="",
#                                                 status="پرداخت شده",
#                                                 notes=""
#                                             )
#                                     elif customer.role == 'هردو':
                                        
#                                         create_both_party_sale_ledger(
#                                             customer=customer,
#                                             sale_instance=sale_instance,
#                                             sale_item=sale_item,
#                                             total_amount=should_paid,
#                                             paid_amount=paid_amount_for_every_record,
#                                             remain_amount=sale_item.borrow_amount
#                                         )

#                                 else:
#                                     raise ValueError('محصول در گدام موجود نیست')

#                     for obj in sale_item_formset.deleted_objects:
#                         obj.delete()

#                     messages.success(request, 'فروش و آیتم‌ها موفقانه ثبت شدند')
#                     return redirect('Order:Direct_sale')

            
#             except Exception as e:
#                 messages.error(request, f'خطا در هنگام ثبت فروش: {str(e)}')
#                 return redirect('Order:Direct_sale')
#         else:
            

#             return HttpResponse(
#                 f"مشکل ثبت فروش\n"
#                 f"Form errors: {my_form.errors}\n"
#                 f"Formset errors: {sale_item_formset.errors}\n"
                
#             )

#     context = {
#         'products': products,
#         'my_date': my_date,
#         'warehouses': warehouses,
#         'my_form': my_form,
#         'sale_item_formset': sale_item_formset,
#         'total_should_paid':total_should_paid,
#         'customer_list':customer_list,
#         'summary':summary,
#     }
#     return render(request, 'Order/Direct_sale.html', context)

import os
from reportlab.lib.pagesizes import A4, landscape
  
def reshape_text(text):
    """Reshape Persian text for correct display in PDF"""
    return get_display(arabic_reshaper.reshape(text))

def generate_sale_item_pdf(request):
    """Generate a PDF report for all sale_item_part records"""
    
    # Fetch all sale_item_part records
    all_sales = sale_item_part.objects.all()

    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sale_items_report.pdf"'

    # Register a better font for Persian/Arabic text
    font_path = staticfiles_storage.path('fonts/Amiri-Regular.ttf')  # Path to the font file
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Amiri', font_path))
        font_name = 'Amiri'
    else:
        pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
        font_name = 'Arial'

    # Create a PDF document
    doc = SimpleDocTemplate(response, pagesize=landscape(A4))  # Use landscape mode
    elements = []

    # Define custom Persian/Arabic text style
    styles = getSampleStyleSheet()
    persian_style = ParagraphStyle(
        name='PersianStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        alignment=1,  # Center alignment
    )

    # Title
    title_text = "لیست PDF شده همه فروشات"
    title = Paragraph(reshape_text(title_text), persian_style)
    elements.append(title)
    elements.append(Spacer(1, 20))  # Add space after the title

    # Table Headers
    headers = [
        reshape_text("یادداشت‌ها"),
        reshape_text("مقدار باقی‌مانده"), 
        reshape_text("مبلغ پرداخت شده"), 
        reshape_text("مبلغ قابل پرداخت"), 
        reshape_text("قیمت واحد"), 
        reshape_text("وزن"), 
        reshape_text("تعداد"), 
        reshape_text("محصول"), 
        reshape_text("نام مشتری"), 
        reshape_text("تاریخ ثبت"), 
        reshape_text("شماره سفارش"), 

    ]

    # Table Data
    data = [headers]

    for order in all_sales:
        data.append([
            reshape_text(order.notes or "-"),
            str(order.borrow_amount),
            str(order.paid_amount_for_every_record),
            str(order.should_paid),
            str(order.price_per_unit),
            str(order.weight),
            str(order.quantity),
            reshape_text(order.product.meat_name),
            reshape_text(order.sell_forei.customer.name) if order.sell_forei and order.sell_forei.customer else "-",
            str(order.sell_forei.reg_date) if order.sell_forei else "-",
            str(order.id),

        ])

    # Create a Table
    PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)  # Use landscape mode

    # Define table column widths dynamically
    total_columns = len(headers)
    col_width = PAGE_WIDTH / total_columns  # Equal column width
    col_widths = [col_width] * total_columns  # Set all columns to equal width

    # Create table
    table = Table(data, colWidths=col_widths)
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

    # Build the PDF
    doc.build(elements)
    return response
    




def delete_sale(request, sale_item_id):
    try:
        with transaction.atomic():
            sale_item = get_object_or_404(sale_item_part, id=sale_item_id)
            customer_obj = sale_item.sell_forei.customer

            system_all_money = total_balance.objects.first()
            inventory_record = inventrories.objects.filter(
                sale_forignkey=sale_item,
                product_foerignkey=sale_item.product,
                warehouse_foerignkey=sale_item.warehouse
            ).last()

            if not system_all_money:
                messages.error(request, 'سیستم بالانس موجود نیست.')
                return redirect('Order:Direct_sale')

            # reverse paid money from system
            system_all_money.total_money_in_system -= Decimal(sale_item.paid_amount_for_every_record or 0)
            system_all_money.save()

            # =========================
            # old customer logic kept
            # new both-party logic added
            # =========================
            if customer_obj.role == 'مشتری':
                related_loans = Loan.objects.filter(sale_id=sale_item).first()

                if related_loans:
                    find_the_remain_amount = Decimal(related_loans.sale_id.borrow_amount or 0)
                    find_the_customer_id = related_loans.sale_id.sell_forei.customer_id

                    find_the_sloan_for_supp = Loan.objects.filter(customer_id=find_the_customer_id).last()
                    if find_the_sloan_for_supp:
                        mines_from_total_remian = Decimal(find_the_sloan_for_supp.total_amount or 0) - find_the_remain_amount
                        find_the_sloan_for_supp.total_amount = mines_from_total_remian
                        find_the_sloan_for_supp.save()

                    related_loans.delete()

            elif customer_obj.role == 'هردو':
                BothPartyLedger.objects.filter(
                    customer=customer_obj,
                    sale=sale_item,
                    entry_type='sale'
                ).delete()

            if inventory_record:
                inventory_record.delete()

            sale_item.delete()

            # recalculate ledger only for both-person
            if customer_obj.role == 'هردو':
                recalculate_both_party_ledger(customer_obj)

            messages.success(request, 'رکورد موفقانه حذف گردید و تغییرات اعمال شدند.')
            return redirect('Order:Direct_sale')

    except Exception as e:
        messages.error(request, f'خطا در حذف رکورد فروش: {str(e)}')
        return redirect('Order:Direct_sale')






def return_order(request, sale_id):
    sale = get_object_or_404(sale_item_part, id=sale_id)
    moqdar_aslee = sale.quantity
    moqdar_har_yake = sale.price_per_unit
    tedad_ya_wazan = sale.weight
    total_paisa_pardakhte = sale.should_paid
    total_paisa_dada_shoda = sale.total_amount
    loan = sale.borrow_amount
    all_system_money = total_balance.objects.first()
    all_money = all_system_money.total_money_in_system
    return_instance = Return.objects.get(sale=sale_id)


    if request.method == 'POST':
        my_forms = ReturnForm(request.POST)
        if my_forms.is_valid():
            moqdar_bargashte = my_forms.cleaned_data['quantity']
            qemat_fee_wahid = my_forms.cleaned_data['price_per']
            wazan_ya_tedad = my_forms.cleaned_data['weight']
            sale.sale = id
            sale.save()
            if moqdar_bargashte <= moqdar_aslee and wazan_ya_tedad <= tedad_ya_wazan:
                total_bargashte = moqdar_bargashte * qemat_fee_wahid
                if total_bargashte <= loan:
                    mines_from_system = loan - total_bargashte
                    sale.borrow_amount = mines_from_system
                    sale.save()
                else:
                    mines_from_system_total_money = all_money - Decimal(total_bargashte)
                    all_system_money.total_money_in_system = mines_from_system_total_money
                    all_system_money.save()
                # Update the Sale object first
                mines_from_total_of_jens = total_paisa_pardakhte - total_bargashte
                sale.should_paid = mines_from_total_of_jens
                sale.save()

                mines_amount = moqdar_aslee - moqdar_bargashte
                sale.quantity = mines_amount
                mnes_weight = tedad_ya_wazan - wazan_ya_tedad
                sale.weight = mnes_weight
                sale.save()

                # Now process the return record
                return_instance = my_forms.save(commit=False)
                return_instance.sale = sale
                return_instance.save()

                messages.success(request, 'برگشت موفقانه ثبت شد')
                return redirect('Order:Direct_sale')
            else:
                messages.warning(request, 'مقدار برگشتی بیشتر از موجودی است')
                return redirect('Order:Direct_sale')
        else:
            messages.warning(request, 'مشکل موجود بوده بازگشت ثبت نشد')
            return redirect('Order:Direct_sale')

    else:
        return_instance = Return.objects.get(sale=sale_id)
        my_forms = ReturnForm(initial={'sale': sale})
        context = {
            'return_instance':return_instance,
            'sale': sale,
            'my_forms': my_forms,
        }
        return render(request, 'Order/return_sale.html', context)

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



def edit_Direct_sale(request, id):
    sale_instance = get_object_or_404(Sale, id=id)
    old_customer_obj = sale_instance.customer
    customer = sale_instance.customer.id
    system_all_money = total_balance.objects.first()
    
    SaleForm = modelform_factory(Sale, fields=('customer', 'reg_date'))
    SaleItemFormset = inlineformset_factory(Sale, sale_item_part, form=sale_itemForm, extra=0, can_delete=True)
    old_both_customer = None
    if request.method == 'POST':
        my_form = SaleForm(request.POST, instance=sale_instance)
        sale_item_formset = SaleItemFormset(request.POST, instance=sale_instance)

        if my_form.is_valid() and sale_item_formset.is_valid():
            try:
                with transaction.atomic():
                    old_both_customer = None
           
                    find_inventory = inventrories.objects.filter(sale_forignkey__sell_forei=sale_instance,in_and_out='OUT')
                    delte_obj = find_inventory.delete()


                    for i in sale_instance.sale_item_part_set.all():
                        find_the_paid_amount = i.paid_amount_for_every_record
                        find_system_money = system_all_money.total_money_in_system - Decimal(find_the_paid_amount)
                        system_all_money.total_money_in_system = find_system_money
                        system_all_money.save()
                
                    
                    loan_amounts = []
                    if old_customer_obj.role == 'مشتری':
                        for item in sale_instance.sale_item_part_set.all():
                            find_remain_Amount = item.borrow_amount

                            loan = Loan.objects.get(customer=customer,sale_id=item)
                            find_last_user_loan = Loan.objects.filter(customer=customer).last()
                            mines_from_toal_borrow = find_last_user_loan.total_amount - find_remain_Amount
                            find_last_user_loan.total_amount = mines_from_toal_borrow
                            find_last_user_loan.save()
                            loan_amounts.append(loan.amount)
                            loan.delete()
                    elif old_customer_obj.role == 'هردو':
                        old_both_customer = old_customer_obj
                        BothPartyLedger.objects.filter(
                            customer=old_customer_obj,
                            sale__sell_forei=sale_instance,
                            entry_type='sale'
                        ).delete()
                    

                 
                    
                    # 2. Process the updated sale
                    customer = my_form.cleaned_data.get('customer')
                    date = my_form.cleaned_data.get('reg_date')
                    updated_sale = my_form.save()
                    
                    # 3. Process each updated sale item
                    for form in sale_item_formset:
                        if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                            sale_item = form.save(commit=False)
                            quantity = form.cleaned_data.get('quantity')
                            weight = form.cleaned_data.get('weight')
                            price_per_unit = form.cleaned_data.get('price_per_unit')
                            paid_amount = form.cleaned_data.get('paid_amount_for_every_record')
                            product_instance = form.cleaned_data.get('product')
                            warehouse_instance = form.cleaned_data.get('warehouse')
                            status = form.cleaned_data.get('status')

                            # Check inventory availability (same as your sale view)
                            all_data = inventrories.objects.select_for_update().filter(
                                warehouse_foerignkey=warehouse_instance,
                                product_foerignkey=product_instance
                            )

                            find_purchase_date = inventrories.objects.filter(
                                warehouse_foerignkey=warehouse_instance,
                                product_foerignkey=product_instance,
                                in_and_out='IN'
                            ).values(
                                'product_foerignkey', 'product_foerignkey__meat_name'
                            ).annotate(
                                total_weight_in_purchase=Sum('weight_field'),
                                total_quantity_in_purchase=Sum('Quantity')
                            )

                            find_sell_date = inventrories.objects.filter(
                                warehouse_foerignkey=warehouse_instance,
                                product_foerignkey=product_instance,
                                in_and_out='OUT'
                            ).values(
                                'product_foerignkey', 'product_foerignkey__meat_name'
                            ).annotate(
                                total_weight_in_sell=Sum('weight_field'),
                                total_quantity_in_sell=Sum('Quantity')
                            )

                            sell_data_dict = {item['product_foerignkey']: item for item in find_sell_date}

                            for purchase in find_purchase_date:
                                product_id = purchase['product_foerignkey']
                                total_weight_in = purchase['total_weight_in_purchase'] or 0
                                total_quantity_in = purchase['total_quantity_in_purchase'] or 0

                                total_weight_out = sell_data_dict.get(product_id, {}).get('total_weight_in_sell', 0)
                                total_quantity_out = sell_data_dict.get(product_id, {}).get('total_quantity_in_sell', 0)

                                weight_difference = total_weight_in - total_weight_out
                                quantity_difference = total_quantity_in - total_quantity_out

                                # Calculate financials (same as your sale view)
                                if status == 'ضرب وزن':
                                    should_paid = round(weight * price_per_unit)
                                else:
                                    should_paid = round(quantity * price_per_unit)

                                borrow_amount = should_paid - paid_amount

                                # Update sale item
                                sale_item.should_paid = should_paid
                                sale_item.borrow_amount = borrow_amount
                                sale_item.sell_forei = updated_sale
                                sale_item.reamin_amount_according_to_sale_record = borrow_amount
                                sale_item.save()

                                # Update system money
                                if system_all_money and Decimal(should_paid) > 0:
                                    system_all_money.total_money_in_system += Decimal(paid_amount)
                                    system_all_money.save()

                                # Recreate inventory record
                                inventrories.objects.create(
                                    product_foerignkey=product_instance,
                                    warehouse_foerignkey=warehouse_instance,
                                    sale_forignkey=sale_item,
                                    Quantity=quantity,
                                    weight_field=weight,
                                    in_and_out='OUT'
                                )
                                    

                                # Handle loans (same as your sale view)
                                if customer.role == 'مشتری':
                                    if borrow_amount != 0:
                                        latest_loan = Loan.objects.filter(customer_id=customer.id).order_by('-id').first()
                                        total_amount = Decimal(latest_loan.total_amount) if latest_loan else 0
                                        total_amount += Decimal(borrow_amount)
                                        
                                        Loan.objects.create(
                                            customer=customer,
                                            sale_id=sale_item,
                                            amount=borrow_amount,
                                            total_amount=total_amount,
                                            date_issued=date,
                                            due_date="",
                                            status="پرداخت نه شده",
                                            notes=""
                                        ) 
                                    else:
                                        latest_loan = Loan.objects.filter(customer_id=customer.id).order_by('-id').first()
                                        total_amount = Decimal(latest_loan.total_amount) if latest_loan else 0
                                        
                                        Loan.objects.create(
                                            customer=customer,
                                            sale_id=sale_item,
                                            amount=should_paid,
                                            total_amount=total_amount,
                                            date_issued=date,
                                            due_date="",
                                            status="پرداخت شده",
                                            notes=""
                                        )
                                elif customer.role == 'هردو':
                                    BothPartyLedger.objects.create(
                                        customer=customer,
                                        entry_type='sale',
                                        date=date,
                                        sale=sale_item,
                                        total_amount=Decimal(should_paid),
                                        paid_amount=Decimal(paid_amount or 0),
                                        remain_amount=Decimal(borrow_amount or 0),
                                        previous_supplier_balance=Decimal('0'),
                                        previous_customer_balance=Decimal('0'),
                                        current_supplier_balance=Decimal('0'),
                                        current_customer_balance=Decimal('0'),
                                        note='ویرایش فروش برای شخص هردو'
                                    )
                    if old_both_customer:
                        recalculate_both_party_ledger(old_both_customer)

                    if customer.role == 'هردو':
                        recalculate_both_party_ledger(customer)

                    messages.success(request, 'فروش با موفقیت ویرایش شد')
                    return redirect('Order:Direct_sale')
            except Exception as e:
                messages.error(request, f'خطا در هنگام ثبت فروش: {str(e)}')
                return redirect('Order:Direct_sale')

        else:
            messages.error(request, "مشکل در اعتبارسنجی فرم‌ها")
            return redirect('Order:Direct_sale')
    else:
        my_form = SaleForm(instance=sale_instance)
        my_form.fields['customer'].queryset = Customer.objects.filter(role__in=['مشتری', 'هردو'])
        sale_item_formset = SaleItemFormset(instance=sale_instance)
    
    context = {
        'my_form': my_form,
        'sale_item_formset': sale_item_formset,
        'sale_instance': sale_instance,
    }
    return render(request, "Order/edit_Direct_sale.html", context)




def bill_details(request, id):
    record = sale_item_part.objects.get(id=id)
    fetch = record.sell_forei_id

    recent_records = sale_item_part.objects.filter(sell_forei_id=fetch) 
    total_sum = recent_records.aggregate(total=Sum('paid_amount_for_every_record'))['total'] or 0
    total_min = recent_records.aggregate(total=Sum('borrow_amount'))['total'] or 0

    context = {
        'recent_records':recent_records,
        'record':record,
        'total_sum':total_sum,
        'total_min':total_min,

    }
    return render(request, 'Order/bill.html',context)






def full_details(request, sale_id):
    # Retrieve the sale record
    sale = get_object_or_404(Sale, id=sale_id)

    # Retrieve related Return_Details records (if any)
    return_details = Return_Details.objects.filter(customer_of_sale=sale.customer)

    # Pass the data to the template
    context = {
        'sale': sale,
        'return_details': return_details,
    }

    return render(request, 'Order/full_details.html', context)



def sale_details(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    if request.method == 'POST':
        my_forms = ReturnForm(request.POST)
        if my_forms.is_valid():
            return_instance = my_forms.save(commit=False)
            return_instance.sale = sale
            total_balancess = Decimal(return_instance.quantity) * Decimal(sale.price_per_unit)
            if sale.quantity >= return_instance.quantity:
                sale.quantity -= return_instance.quantity
                sale.total_amount = Decimal(sale.quantity) * Decimal(sale.price_per_unit)
                sale.save()
                return_instance.save()

                total_balances = total_balance.objects.first()
                if total_balances:
                    if total_balances.total_money_in_system is None:
                        total_balances.total_money_in_system = Decimal(0)
                    total_balances.total_money_in_system -= total_balancess
                    total_balances.save()

                    print({
                        'customer_of_sale': sale.customer,
                        'product_of_sale': sale.product,
                        'quantity_of_sale': str(sale.quantity),
                        'total_amount_of_sale': str(sale.total_amount),
                        'price_per_unit_of_sale': str(sale.price_per_unit),
                        'rerun_of_quantity': str(return_instance.quantity),
                    })

                    Return_Details.objects.create(
                        customer_of_sale=sale.customer,
                        product_of_sale=sale.product,
                        quantity_of_sale=str(sale.quantity),
                        total_amount_of_sale=str(sale.total_amount),
                        price_per_unit_of_sale=str(sale.price_per_unit),
                        rerun_of_quantity=str(return_instance.quantity),
                    )

                    messages.success(
                        request,
                        f'بازگشت موفقانه ثبت شد. مبلغ کل بازگشتی: {total_balancess} افغانی. '
                        f'موجودی جدید در سیستم: {total_balances.total_money_in_system} افغانی. '
                        f'مبلغ جدید فروش: {sale.total_amount} افغانی.'
                    )
                else:
                    messages.warning(
                        request,
                        'خطا: موجودی کل سیستم یافت نشد. لطفاً ابتدا موجودی کل سیستم را تنظیم کنید.'
                    )
            else:
                messages.warning(
                    request,
                    'بازگشت ناموفق بود: مقدار بازگشتی بیشتر از مقدار فروخته شده است.'
                )
                return redirect('Order:Direct_sale')

            messages.success(request, 'برگشت موفقانه ثبت شد')
            return redirect('Order:Direct_sale')
        else:
            messages.warning(request, 'مشکل موجود بوده بازگشت ثبت نشد')
            return redirect('Order:Direct_sale')
    else:
        my_forms = ReturnForm(initial={'sale': sale})
        context = {
            'sale': sale,
            'my_forms': my_forms,
        }

    return render(request, 'Order/sale_details.html', context)









def order_loans(request):
    system_all_money = total_balance.objects.first()
    first_record = system_all_money.total_money_in_system

    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        record = get_object_or_404(Sale, id=record_id)
        loan_amount = record.borrow_amount
        paid_amou = record.total_amount
        my_form = order_loanForm(request.POST)
        if my_form.is_valid():
            second_pay = my_form.cleaned_data['pay_amount']
            if second_pay <= loan_amount and second_pay > 0:
                mines_from_total_loan = loan_amount - second_pay
                sum_of_this_paid_amount = paid_amou + second_pay
                record.total_amount = sum_of_this_paid_amount
                record.borrow_amount = mines_from_total_loan
                system_all_money.total_money_in_system += second_pay
                system_all_money.save()
                record.save()
                record.save()
            else:
                messages.warning(request, f'مقدار {second_pay} بزرگتر از مقدار است که باید پرداخت شود')
                return redirect('Order:order_loans')
            my_form.save()
            messages.success(request, 'باقی قرض موفقانه اجرا شد ')
            return redirect('Order:order_loans')
        else:
            messages.warning(request,'مشکل موجود است')
            return redirect('Order:order_loans')
    else:
        records = Sale.objects.filter(borrow_amount__gt=0)
        my_form = order_loanForm()

    context = {
        'records':records,
        'my_form':my_form
    }

    return render(request, 'Order/loans.html', context)



def get_product_available_stock(product_instance):
    product_id = product_instance.id

    # IN from purchases
    purchase_data = Parchase.objects.filter(product=product_id).aggregate(
        total_qty=Sum('quantity'),
        total_weight=Sum('wegiht'),
    )
    purchase_qty = purchase_data['total_qty'] or 0
    purchase_weight = purchase_data['total_weight'] or 0

    # IN from item_deals  receipt
    receipt_data = item_deals.objects.filter(
        item=product_id,
        status='رسید'
    ).aggregate(
        total_qty=Sum('number'),
        total_weight=Sum('weighht'),
    )
    receipt_qty = receipt_data['total_qty'] or 0
    receipt_weight = receipt_data['total_weight'] or 0

    # OUT from direct sales
    sale_data = sale_item_part.objects.filter(product=product_id).aggregate(
        total_qty=Sum('quantity'),
        total_weight=Sum('weight'),
    )
    sale_qty = sale_data['total_qty'] or 0
    sale_weight = sale_data['total_weight'] or 0

    # OUT from item_deals برداشت
    withdraw_data = item_deals.objects.filter(
        item=product_id,
        status='برداشت'
    ).aggregate(
        total_qty=Sum('number'),
        total_weight=Sum('weighht'),
    )
    withdraw_qty = withdraw_data['total_qty'] or 0
    withdraw_weight = withdraw_data['total_weight'] or 0

    available_quantity = (purchase_qty + receipt_qty) - (sale_qty + withdraw_qty)
    available_weight = (purchase_weight + receipt_weight) - (sale_weight + withdraw_weight)

    return {
        'available_quantity': Decimal(str(available_quantity or 0)),
        'available_weight': Decimal(str(available_weight or 0)),
    }


def Direct_sale(request):
    summary = (
        sale_item_part.objects.values('product__id', 'product__meat_name').annotate(
            total_quantity=Sum('quantity'),
            total_weight=Sum('weight')
        )
    )

    SaleItemFormSet = modelformset_factory(
        sale_item_part,
        form=sale_itemForm,
        extra=0,
        can_delete=True
    )
    sale_item_formset = SaleItemFormSet(
        request.POST or None,
        queryset=sale_item_part.objects.none()
    )

    find_all_sale_money = sale_item_part.objects.aggregate(
        total_should_paid=Sum('should_paid')
    )
    total_should_paid = find_all_sale_money['total_should_paid'] or 0

    customer_list = Customer.objects.filter(role__in=['مشتری', 'هردو'])
    my_form = SaleForm(request.POST or None)
    products = product.objects.all()
    warehouses = warehouse_info.objects.all()
    my_date = sale_item_part.objects.all().order_by('id')

    system_all_money = total_balance.objects.first()
    if not system_all_money:
        return HttpResponse('پول در سیستم موجود نیست ..!')

    if request.method == 'POST':
        if my_form.is_valid() and sale_item_formset.is_valid():
            try:
                with transaction.atomic():
                    customer = my_form.cleaned_data.get('customer')
                    sale_instance = my_form.save()

                    sale_items = sale_item_formset.save(commit=False)

                    for form, sale_item in zip(sale_item_formset.forms, sale_items):
                        if not form.cleaned_data:
                            continue

                        quantity = form.cleaned_data.get('quantity') or 0
                        weight = form.cleaned_data.get('weight') or 0
                        price_per_unit = form.cleaned_data.get('price_per_unit') or 0
                        paid_amount_for_every_record = form.cleaned_data.get('paid_amount_for_every_record') or 0
                        product_instance = form.cleaned_data.get('product')
                        warehouse_instance = form.cleaned_data.get('warehouse')
                        status = form.cleaned_data.get('status')

                        quantity = Decimal(str(quantity))
                        weight = Decimal(str(weight))
                        price_per_unit = Decimal(str(price_per_unit))
                        paid_amount_for_every_record = Decimal(str(paid_amount_for_every_record))

                        # Lock system balance row
                        system_all_money = total_balance.objects.select_for_update().first()
                        if not system_all_money:
                            raise ValueError('پول در سیستم موجود نیست')

                        # Calculate stock exactly like your existence page
                        stock = get_product_available_stock(product_instance)
                        available_quantity = stock['available_quantity']
                        available_weight = stock['available_weight']

                        # Validation based on sale type
                        if status == 'ضرب وزن':
                            if weight > available_weight:
                                raise ValueError(
                                    f'وزن کافی در گدام موجود نیست. موجودی فعلی {available_weight}'
                                )
                            should_paid = round(weight * price_per_unit)
                        else:
                            if quantity > available_quantity:
                                raise ValueError(
                                    f'تعداد کافی در گدام موجود نیست. موجودی فعلی {available_quantity}'
                                )
                            should_paid = round(quantity * price_per_unit)

                        borrow_amount = Decimal(str(should_paid)) - paid_amount_for_every_record

                        sale_item.should_paid = should_paid
                        sale_item.borrow_amount = borrow_amount
                        sale_item.sell_forei = sale_instance
                        sale_item.reamin_amount_according_to_sale_record = borrow_amount
                        sale_item.save()

                        # keep inventory OUT record if you still want inventory history
                        inventrories.objects.create(
                            product_foerignkey=product_instance,
                            warehouse_foerignkey=warehouse_instance,
                            sale_forignkey=sale_item,
                            Quantity=quantity,
                            weight_field=weight,
                            in_and_out='OUT'
                        )

                        # add paid money to system
                        if paid_amount_for_every_record > 0:
                            system_all_money.total_money_in_system += paid_amount_for_every_record
                            system_all_money.save()

                        # Customer loan logic
                        if customer.role == 'مشتری':
                            latest_unpaid_loan = Loan.objects.filter(
                                customer_id=customer.id
                            ).order_by('-id').first()

                            previous_total = Decimal(
                                str(latest_unpaid_loan.total_amount)
                            ) if latest_unpaid_loan else Decimal('0')

                            if borrow_amount != 0:
                                total_amount = previous_total + borrow_amount
                                Loan.objects.create(
                                    customer=my_form.instance.customer,
                                    sale_id=sale_item,
                                    amount=borrow_amount,
                                    total_amount=total_amount,
                                    date_issued=my_form.instance.reg_date,
                                    due_date="",
                                    status="پرداخت نه شده",
                                    notes=""
                                )
                            else:
                                sale_item.is_money_approved = True
                                sale_item.save(update_fields=['is_money_approved'])

                                Loan.objects.create(
                                    customer=my_form.instance.customer,
                                    sale_id=sale_item,
                                    amount=should_paid,
                                    total_amount=previous_total,
                                    date_issued=my_form.instance.reg_date,
                                    due_date="",
                                    status="پرداخت شده",
                                    notes=""
                                )

                        elif customer.role == 'هردو':
                            create_both_party_sale_ledger(
                                customer=customer,
                                sale_instance=sale_instance,
                                sale_item=sale_item,
                                total_amount=should_paid,
                                paid_amount=paid_amount_for_every_record,
                                remain_amount=borrow_amount
                            )

                    for obj in sale_item_formset.deleted_objects:
                        obj.delete()

                    messages.success(request, 'فروش و آیتم‌ها موفقانه ثبت شدند')
                    return redirect('Order:Direct_sale')

            except Exception as e:
                messages.error(request, f'خطا در هنگام ثبت فروش: {str(e)}')
                return redirect('Order:Direct_sale')

        return HttpResponse(
            f"مشکل ثبت فروش\n"
            f"Form errors: {my_form.errors}\n"
            f"Formset errors: {sale_item_formset.errors}\n"
        )

    context = {
        'products': products,
        'my_date': my_date,
        'warehouses': warehouses,
        'my_form': my_form,
        'sale_item_formset': sale_item_formset,
        'total_should_paid': total_should_paid,
        'customer_list': customer_list,
        'summary': summary,
    }
    return render(request, 'Order/Direct_sale.html', context)