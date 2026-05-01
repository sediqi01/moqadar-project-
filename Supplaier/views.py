from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from .forms import *
from Order.models import *
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from purchase.models import *
from django.db.models import Sum
from Customer.models import SLoan
from Customer.forms import SLoanForm
from decimal import Decimal
from django.db.models import OuterRef, Subquery

from django.db import transaction, DatabaseError
from decimal import Decimal
from django.db.models import OuterRef, Subquery, F, Value, Case, When, DecimalField
from django.db.models.functions import Coalesce


def supplaier(request):
    if request.method == 'POST':
        my_form = SupplaierForm(request.POST)
        if my_form.is_valid():
            try:
                with transaction.atomic():
                    is_customer = request.POST.get('type', False)  # Default to False if not checked
                    is_customer = True if is_customer == 'on' else False
                    if is_customer:
                        customer_instance = my_form.save(commit=False)
                        customer_instance.role = 'هردو'
                    else:
                        customer_instance = my_form.save(commit=False)
                        customer_instance.role = 'تامین کننده' 
                    customer_instance.save()
                    my_form.save()
                    messages.success(request, ' تامین کننده موفقانه ثبت شد')
                    return redirect('Supplaier:supplaier')
            except Exception as e:
                messages.error(request, 'خطا در ثبت اطلاعات، دوباره تلاش کنید')
                return redirect('Supplaier:supplaier')
    else:
        collect_all = 0
        sum_of_total_amount = 0 
        total_paid_amount = SLoan.objects.filter(
            status='پرداخت شده'
        ).exclude(
            notes__isnull=True
        ).exclude(
            notes=''
        ).aggregate(
            total_amount_sum=Sum('amount')
        )['total_amount_sum'] or 0


        sum_of_all_sale = Parchase.objects.all()
        total_paid_amoun = sum_of_all_sale.aggregate(total=Sum('paid_amount'))['total']
        find_all_paid_from_bothpartyledger = BothPartyLedger.objects.filter(entry_type='pay_to_partner').aggregate(total_paid=Sum('paid_amount'))
        total_paid = find_all_paid_from_bothpartyledger['total_paid'] or 0
        
        collect_all = (total_paid_amoun or 0) + (total_paid_amount or 0) + float(total_paid or 0)

        # latest_loans = SLoan.objects.filter(customer_id=OuterRef('id')).order_by('-id')

        # my_data = Customer.objects.filter(role__in=['تامین کننده', 'هردو']).annotate(
        #     total_borrow=Subquery(latest_loans.values('total_amount')[:1])
        # )

        # latest_loans = SLoan.objects.filter(customer=OuterRef('customer')).order_by('-created').values('id')[:1]
        # loans_with_latest = SLoan.objects.filter(id__in=Subquery(latest_loans))
        # total_sum = loans_with_latest.aggregate(total_amount_sum=Sum('total_amount'))['total_amount_sum'] or 0 
                
        
        latest_loans = SLoan.objects.filter(
            customer=OuterRef('id')
        ).order_by('-id')

        latest_ledger = BothPartyLedger.objects.filter(
            customer_id=OuterRef('id')
        ).order_by('-id')

        my_data = Customer.objects.filter(
            role__in=['تامین کننده', 'هردو']
        ).annotate(
            total_borrow=Coalesce(
                Subquery(latest_loans.values('total_amount')[:1]),
                Value(Decimal('0.00')),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),

            supplier_balance=Coalesce(
                Subquery(latest_ledger.values('current_supplier_balance')[:1]),
                Value(Decimal('0.00')),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            customer_balance=Coalesce(
                Subquery(latest_ledger.values('current_customer_balance')[:1]),
                Value(Decimal('0.00')),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
        ).annotate(
            ledger_due=Case(
                When(
                    supplier_balance__gt=F('customer_balance'),
                    then=F('supplier_balance') - F('customer_balance')
                ),
                default=Value(Decimal('0.00')),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        ).annotate(
            supplier_due=Case(
                When(role='تامین کننده', then=F('total_borrow')),
                When(role='هردو', then=F('ledger_due')),
                default=Value(Decimal('0.00')),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
        total_sum = my_data.aggregate(
            total=Sum('supplier_due')
        )['total'] or 0

        my_form = SupplaierForm()
        context = {
            'total_sum':total_sum,
            'my_form':my_form,
            'collect_all':collect_all,
            'my_data':my_data,
        }

    return render(request, 'supplaier/supplaier.html', context)

def edit_supplaier(request, id):
    # Fetch the customer instance
    customer_instance = Customer.objects.get(pk=id)

    if request.method == "POST":
        # Initialize the form with POST data
        edit_daily_project_form = SupplaierForm(instance=customer_instance, data=request.POST)

        # Handle the 'type' checkbox
        is_customer = request.POST.get('type', False)  # Default to False if unchecked
        is_customer = True if is_customer == 'on' else False

        if edit_daily_project_form.is_valid():
            # Save changes with the correct role
            customer_instance = edit_daily_project_form.save(commit=False)
            customer_instance.role = 'هردو' if is_customer else 'تامین کننده'
            customer_instance.save()

            messages.success(request, 'تغییرات در تامین کننده ذیل موفقانه انجام پذیرفت')
            return HttpResponseRedirect(reverse("Supplaier:supplaier"))
        else:
            messages.warning(request, 'خطایی رخ داد، لطفاً مجدداً تلاش کنید')

    else:
        # Set the initial value of the checkbox based on the role
        initial_checkbox_value = 'checked' if customer_instance.role == 'هردو' else ''

        edit_daily_project_form = SupplaierForm(instance=customer_instance)
        context = {
            'edit_daily_project_form': edit_daily_project_form,
            'id': id,
            'initial_checkbox_value': initial_checkbox_value,
        }
        return render(request, "supplaier/edit_supplaier.html", context)













def supplaer_info(request, id):
    all_data = Customer.objects.get(id=id)
    customer_loan = SLoan.objects.filter(customer_id = id)
    sale_ids = customer_loan.values_list('sale_id', flat=True)
    total_sale_amount = Parchase.objects.filter(id__in=sale_ids).aggregate(
    paid_amount_sum=Sum('paid_amount')
    )['paid_amount_sum'] or 0

    customer_loan_sum = SLoan.objects.filter(
        customer_id=id,
        status='پرداخت شده'
    ).exclude(
        notes__isnull=True  
    ).exclude(
        notes=''  
    ).aggregate(
        total_amount_sum=Sum('amount')
    )['total_amount_sum'] or 0


    total_paid_amount = round(total_sale_amount + customer_loan_sum)
    total_borrow = SLoan.objects.filter(customer_id=id).last()
    total_reamin = round(total_borrow.total_amount)

    # total_paid_amount = Parchase.objects.filter(supplaier=id).aggregate(total_paid=Sum('paid_amount'))['total_paid']
    # total_reamin = Parchase.objects.filter(supplaier=id).aggregate(remain_amount=Sum('remain_amount'))['remain_amount']
    sum_of_all = Parchase.objects.filter(supplaier=id).aggregate(total_unit=Sum('total_unit'))['total_unit']

    try:
        last_record = Parchase.objects.filter(supplaier=id).latest('product')
    except Parchase.DoesNotExist:
        last_record = None
    
    all_records = Parchase.objects.filter(supplaier=id)

    context = {
        'all_data': all_data,
        'total_paid_amount': total_paid_amount,
        'total_reamin': total_reamin,
        'sum_of_all': sum_of_all,
        'last_record': last_record,
        'all_records': all_records,
    }

    return render(request, 'supplaier/suppliaer_more_info.html', context)




def delete_supplaier(request, id):
   
    Purchase_instance = get_object_or_404(Customer, id=id)
    
    
    Purchase_instance.delete()
    messages.success(request, 'تامین کننده موفقانه حذف شد ')
    return redirect('Supplaier:supplaier')  

def delete_paid_record(request,id):
    find_total_money_in_system = total_balance.objects.last()

    find_record =  SLoan.objects.filter(id=id).last()
    find_amount = find_record.amount

    find_user = find_record.customer.id


    find_last_record = SLoan.objects.filter(customer=find_user).last()
    find_last_record.total_amount += find_amount
    find_last_record.save()
    find_total_money_in_system.total_money_in_system += Decimal(find_amount)
    find_total_money_in_system.save()
    find_record.delete()
    messages.success(request, 'ریکارد موفقانه حذف شد ')
    return redirect(request.META.get('HTTP_REFERER', '/'))


def supp_loans(request, id):
    customer = get_object_or_404(Customer, id=id)
    customer_loan = SLoan.objects.filter(customer_id = id).order_by('id')
    sale_ids = customer_loan.values_list('sale_id', flat=True)

   
    total_sale_amount = Parchase.objects.filter(id__in=sale_ids).aggregate(
    paid_amount_sum=Sum('paid_amount')
    )['paid_amount_sum'] or 0

    customer_loan_sum = SLoan.objects.filter(
        customer_id=id,
        status='پرداخت شده'
    ).exclude(
        notes__isnull=True  
    ).exclude(
        notes=''  
    ).aggregate(
        total_amount_sum=Sum('amount')
    )['total_amount_sum'] or 0


    find_all_total_sale_amount = round(total_sale_amount + customer_loan_sum)

    latest_unpaid_loan = SLoan.objects.filter(customer_id=customer.id).order_by('-id').first()
    total_borrow = SLoan.objects.filter(customer_id=id).last()
    total_borrow_amount = round(total_borrow.total_amount)


    latest_unpaid_loan = SLoan.objects.filter(customer_id=customer.id).order_by('-id').first()


    if not latest_unpaid_loan:
        latest_unpaid_loan = 0
    else:
        latest_unpaid_loan = Decimal(latest_unpaid_loan.total_amount)

    latest_paid_loan = SLoan.objects.filter(customer_id=customer.id, status='پرداخت شده').order_by('-id').first()

    if not latest_paid_loan:
        latest_paid_loan = 0
    else:
        latest_paid_loan = Decimal(latest_paid_loan.total_amount)


    context = {
        'customer': customer,
        'customer_loan':customer_loan,
        'find_all_total_sale_amount':find_all_total_sale_amount,
        'total_borrow_amount':total_borrow_amount,
     
    }
    return render(request, 'customer/supp_loans.html', context)

from Finance_and_Accounting.models import *

def paid_supp_loans(request, id):
    customer = get_object_or_404(Customer, id=id)
    system_all_money = total_balance.objects.first()
    first_record = system_all_money.total_money_in_system


    latest_unpaid_loan = SLoan.objects.filter(customer_id=customer.id).order_by('-id').first()
    find_total_ammoun = latest_unpaid_loan.total_amount


    if request.method == "POST":
        paid_amount = request.POST.get("amount")

        find_current_balance = float(find_total_ammoun) - float(paid_amount)


        loan_form = SLoanForm(request.POST)
        if loan_form.is_valid():
            # Create a new loan entry based on form data
            new_loan = loan_form.save(commit=False)
            new_loan.customer = customer
            new_loan.total_amount = find_current_balance
              # Link the loan to the current customer
            new_loan.status = 'پرداخت شده'
            
            sum_with_tamen_konenda = first_record - Decimal(paid_amount)
            system_all_money.total_money_in_system = sum_with_tamen_konenda
            system_all_money.save()

            new_loan.save() 
            # Optionally update the status of unpaid loans to 'پرداخت شده'
            messages.success(request, "پول قرض په موفقیت پرداخت شد.")
            return redirect('Supplaier:supp_loans', id=id)  # Redirect to a relevant page
        else:
            messages.error(request, "مشکلی موجود است به موفقیت پرداخت نه شد.")
    else:
        # If GET request, create an empty form
        loan_form = SLoanForm()    
        context = {
            'customer': customer,
            'loan_form':loan_form,
            'amount':find_total_ammoun,
        }
    
        return render(request, 'customer/paid_supp_loans.html', context)
    

def supp_paid_loans(request, id):
    customer = get_object_or_404(Customer, id=id)

    latest_unpaid_loan = SLoan.objects.filter(customer_id=customer.id, status ='پرداخت شده')


    customer_loan_sum = SLoan.objects.filter(
        customer_id=id, status='پرداخت شده'
    ).aggregate(total_amount_sum=Sum('amount'))['total_amount_sum'] or 0


    context = {
            'customer': customer,
            'latest_unpaid_loan':latest_unpaid_loan,
            'customer_loan_sum':customer_loan_sum,
            
        }
    return render(request, 'supplaier/customer_pais_loan.html', context)




