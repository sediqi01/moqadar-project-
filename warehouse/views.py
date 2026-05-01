from django.shortcuts import render,HttpResponse,redirect, get_object_or_404
from.forms import *
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from.models import *
from .models import inventrories
from django.db.models import Sum
from purchase.models import *
from django.db.models import Count
from django.db import transaction
from Order.models import *
# Create your views here.

def warehouse_part(request):
    if request.method == 'POST':
        my_form = warehouse_infoForm(request.POST)
        try:
            with transaction.atomic(): 
                if my_form.is_valid():
                    my_form.save() 
                    messages.success(request, 'گدام موفقانه ثبت شد')
                    return redirect('warehouse:warehouse_part')
                else:
                    messages.warning(request, 'مشکل موجود بوده گدام ثبت نشد')
                    return redirect('warehouse:warehouse_part')
        
        except Exception as e:
            messages.error(request, f'خطای سیستمی در ثبت گدام: {str(e)}')
            return redirect('warehouse:warehouse_part')
    else:
        inventory_data = (
        inventrories.objects.values('product_foerignkey__meat_name') 
        .annotate(total_quantity=Sum('Quantity'))
        .order_by('-total_quantity') 
        )
        last_record = inventrories.objects.last()
        my_data = warehouse_info.objects.all()
        my_form = warehouse_infoForm()
        context = {
            'my_form':my_form,
            'my_data':my_data,
            'last_record':last_record,
            'inventory_data':inventory_data,
        }

    return render(request,'product_and_catago/ware.html',context)





# def ware_data(request,id):
#     all_date = inventrories.objects.filter(warehouse_foerignkey=id).order_by('id')
#     warejouse = warehouse_info.objects.get(id=id)
#     find_Purchase_date = (
#         inventrories.objects.filter(warehouse_foerignkey=id, in_and_out='IN')
#         .values('product_foerignkey', 'product_foerignkey__meat_name')
#         .annotate(
#             total_weight_in_Purchase=Sum('weight_field'),
#             total_quantity_in_Purchase=Sum('Quantity')
#         )
#     )
#     find_sell_date = (
#         inventrories.objects.filter(warehouse_foerignkey=id, in_and_out='OUT')
#         .values('product_foerignkey', 'product_foerignkey__meat_name')
#         .annotate(
#             total_weight_in_sell=Sum('weight_field'),
#             total_quantity_in_sell=Sum('Quantity')
#         )
#     )

#     sell_dict = {item['product_foerignkey']: item for item in find_sell_date}

#     results = []
#     for Purchase_item in find_Purchase_date:
#         product_id = Purchase_item['product_foerignkey']
#         meat_name = Purchase_item['product_foerignkey__meat_name']
        
#         sell_item = sell_dict.get(product_id, {'total_weight_in_sell': 0, 'total_quantity_in_sell': 0})

#         mines_from_Purchase_to_sell = sell_item['total_weight_in_sell'] - Purchase_item['total_weight_in_Purchase']
#         mines_quantity_to_sell = sell_item['total_quantity_in_sell'] - Purchase_item['total_quantity_in_Purchase']

#         results.append({
#             'meat_name': meat_name,
#             'mines_from_Purchase_to_sell': mines_from_Purchase_to_sell,
#             'mines_quantity_to_sell': mines_quantity_to_sell,
#         })
#     in_totals = inventrories.objects.filter(in_and_out='IN',warehouse_foerignkey=id).values(
#         'product_foerignkey__meat_name'
#     ).annotate(
#         total_quantity_in=Sum('Quantity'),
#         total_weight_in=Sum('weight_field')
#     )
#     out_totals = inventrories.objects.filter(in_and_out='OUT',warehouse_foerignkey=id).values(
#         'product_foerignkey__meat_name'
#     ).annotate(
#         total_quantity_out=Sum('Quantity'),
#         total_weight_out=Sum('weight_field')
#     )
#     product_names = set([x['product_foerignkey__meat_name'] for x in in_totals] +
#                         [x['product_foerignkey__meat_name'] for x in out_totals])
 
#     products_data = []
#     find_all_prpducts = product.objects.all()
#     for i in find_all_prpducts:
#         product_id = i.id
#         find_all_purchases_q = Parchase.objects.filter(product=product_id).aggregate(total_quantity_in_Purchase=Sum('quantity'),)
#         purchase_qty = find_all_purchases_q['total_quantity_in_Purchase'] or 0
#         purchase_products_in_item_delas = item_deals.objects.filter(item=product_id,status='رسید').aggregate(total_quantity_in_item_delas=Sum('number'),)
#         item_deals_qty = purchase_products_in_item_delas['total_quantity_in_item_delas'] or 0

#         find_all_purchases_weight = Parchase.objects.filter(product=product_id).aggregate(total_weight_in_Purchase=Sum('wegiht'),)
#         purchase_wigh = find_all_purchases_weight['total_weight_in_Purchase'] or 0
#         purchase_prduct_item_delas_wirght = item_deals.objects.filter(item=product_id,status='رسید').aggregate(total_weight_in_item_delas=Sum('weighht'),)
#         total_wight_in_item_delas_purchase = purchase_prduct_item_delas_wirght['total_weight_in_item_delas'] or 0


#         find_all_sale_q = sale_item_part.objects.filter(product=product_id).aggregate(total_quantity_in_sale=Sum('quantity'))
#         sale_qty = find_all_sale_q['total_quantity_in_sale'] or 0
#         sale_products_in_item_deal_quantity = item_deals.objects.filter(item=product_id,status='برداشت').aggregate(total_quantity_sold_in_item_deals=Sum('number'),)
#         item_deals_qty_sold = sale_products_in_item_deal_quantity['total_quantity_sold_in_item_deals'] or 0

#         find_all_sale_weight = sale_item_part.objects.filter(product=product_id).aggregate(total_wight_in_sale=Sum('weight'),)
#         sold_wight = find_all_sale_weight['total_wight_in_sale'] or 0
#         sold_products_in_item_delas_weight = item_deals.objects.filter(item=product_id,status='برداشت').aggregate(total_weight_sold_in_item_deals=Sum('weighht'))
#         total_weight_in_item_deals_sold = sold_products_in_item_delas_weight['total_weight_sold_in_item_deals'] or 0
                
#         products_data.append({
#             'product_id':product_id,
#             'product_name':i.meat_name,
#             'total_quantity_purchased': purchase_qty + item_deals_qty or 0,
#             'total_weight_purchased': purchase_wigh + total_wight_in_item_delas_purchase or 0,
#             'total_quantity_sold': sale_qty + item_deals_qty_sold or 0,
#             'total_wegiht_sold': sold_wight + total_weight_in_item_deals_sold or 0
#         }) 


   
#     context = {
#         'results': results,
#         'warejouse':warejouse,
#         'all_date':all_date,
#         'products_data':products_data,
#     }
#     return render(request,'product_and_catago/ware_ingo.html',context)




def ware_data(request,id):
    all_date = inventrories.objects.filter(warehouse_foerignkey=id).order_by('id')
    warejouse = warehouse_info.objects.get(id=id)

    # updated only this section: results should calculate like direct sale / products_data
    results = []
    find_all_prpducts_for_results = product.objects.all()

    for i in find_all_prpducts_for_results:
        product_id = i.id

        find_all_purchases_q = Parchase.objects.filter(product=product_id).aggregate(
            total_quantity_in_Purchase=Sum('quantity'),
        )
        purchase_qty = find_all_purchases_q['total_quantity_in_Purchase'] or 0

        purchase_products_in_item_delas = item_deals.objects.filter(
            item=product_id,
            status='رسید'
        ).aggregate(
            total_quantity_in_item_delas=Sum('number'),
        )
        item_deals_qty = purchase_products_in_item_delas['total_quantity_in_item_delas'] or 0

        find_all_purchases_weight = Parchase.objects.filter(product=product_id).aggregate(
            total_weight_in_Purchase=Sum('wegiht'),
        )
        purchase_wigh = find_all_purchases_weight['total_weight_in_Purchase'] or 0

        purchase_prduct_item_delas_wirght = item_deals.objects.filter(
            item=product_id,
            status='رسید'
        ).aggregate(
            total_weight_in_item_delas=Sum('weighht'),
        )
        total_wight_in_item_delas_purchase = purchase_prduct_item_delas_wirght['total_weight_in_item_delas'] or 0

        find_all_sale_q = sale_item_part.objects.filter(product=product_id).aggregate(
            total_quantity_in_sale=Sum('quantity')
        )
        sale_qty = find_all_sale_q['total_quantity_in_sale'] or 0

        sale_products_in_item_deal_quantity = item_deals.objects.filter(
            item=product_id,
            status='برداشت'
        ).aggregate(
            total_quantity_sold_in_item_deals=Sum('number'),
        )
        item_deals_qty_sold = sale_products_in_item_deal_quantity['total_quantity_sold_in_item_deals'] or 0

        find_all_sale_weight = sale_item_part.objects.filter(product=product_id).aggregate(
            total_wight_in_sale=Sum('weight'),
        )
        sold_wight = find_all_sale_weight['total_wight_in_sale'] or 0

        sold_products_in_item_delas_weight = item_deals.objects.filter(
            item=product_id,
            status='برداشت'
        ).aggregate(
            total_weight_sold_in_item_deals=Sum('weighht')
        )
        total_weight_in_item_deals_sold = sold_products_in_item_delas_weight['total_weight_sold_in_item_deals'] or 0

        available_quantity = (purchase_qty + item_deals_qty) - (sale_qty + item_deals_qty_sold)
        available_weight = (purchase_wigh + total_wight_in_item_delas_purchase) - (sold_wight + total_weight_in_item_deals_sold)

        results.append({
            'meat_name': i.meat_name,
            'mines_from_Purchase_to_sell': available_weight,
            'mines_quantity_to_sell': available_quantity,
        })

    in_totals = inventrories.objects.filter(in_and_out='IN',warehouse_foerignkey=id).values(
        'product_foerignkey__meat_name'
    ).annotate(
        total_quantity_in=Sum('Quantity'),
        total_weight_in=Sum('weight_field')
    )
    out_totals = inventrories.objects.filter(in_and_out='OUT',warehouse_foerignkey=id).values(
        'product_foerignkey__meat_name'
    ).annotate(
        total_quantity_out=Sum('Quantity'),
        total_weight_out=Sum('weight_field')
    )
    product_names = set([x['product_foerignkey__meat_name'] for x in in_totals] +
                        [x['product_foerignkey__meat_name'] for x in out_totals])
 
    products_data = []
    find_all_prpducts = product.objects.all()
    for i in find_all_prpducts:
        product_id = i.id
        find_all_purchases_q = Parchase.objects.filter(product=product_id).aggregate(total_quantity_in_Purchase=Sum('quantity'),)
        purchase_qty = find_all_purchases_q['total_quantity_in_Purchase'] or 0
        purchase_products_in_item_delas = item_deals.objects.filter(item=product_id,status='رسید').aggregate(total_quantity_in_item_delas=Sum('number'),)
        item_deals_qty = purchase_products_in_item_delas['total_quantity_in_item_delas'] or 0

        find_all_purchases_weight = Parchase.objects.filter(product=product_id).aggregate(total_weight_in_Purchase=Sum('wegiht'),)
        purchase_wigh = find_all_purchases_weight['total_weight_in_Purchase'] or 0
        purchase_prduct_item_delas_wirght = item_deals.objects.filter(item=product_id,status='رسید').aggregate(total_weight_in_item_delas=Sum('weighht'),)
        total_wight_in_item_delas_purchase = purchase_prduct_item_delas_wirght['total_weight_in_item_delas'] or 0

        find_all_sale_q = sale_item_part.objects.filter(product=product_id).aggregate(total_quantity_in_sale=Sum('quantity'))
        sale_qty = find_all_sale_q['total_quantity_in_sale'] or 0
        sale_products_in_item_deal_quantity = item_deals.objects.filter(item=product_id,status='برداشت').aggregate(total_quantity_sold_in_item_deals=Sum('number'),)
        item_deals_qty_sold = sale_products_in_item_deal_quantity['total_quantity_sold_in_item_deals'] or 0

        find_all_sale_weight = sale_item_part.objects.filter(product=product_id).aggregate(total_wight_in_sale=Sum('weight'),)
        sold_wight = find_all_sale_weight['total_wight_in_sale'] or 0
        sold_products_in_item_delas_weight = item_deals.objects.filter(item=product_id,status='برداشت').aggregate(total_weight_sold_in_item_deals=Sum('weighht'))
        total_weight_in_item_deals_sold = sold_products_in_item_delas_weight['total_weight_sold_in_item_deals'] or 0
                
        products_data.append({
            'product_id':product_id,
            'product_name':i.meat_name,
            'total_quantity_purchased': purchase_qty + item_deals_qty or 0,
            'total_weight_purchased': purchase_wigh + total_wight_in_item_delas_purchase or 0,
            'total_quantity_sold': sale_qty + item_deals_qty_sold or 0,
            'total_wegiht_sold': sold_wight + total_weight_in_item_deals_sold or 0
        }) 

    context = {
        'results': results,
        'warejouse':warejouse,
        'all_date':all_date,
        'products_data':products_data,
    }
    return render(request,'product_and_catago/ware_ingo.html',context)


def delete_warehouse(request, id):
    # Fetch the Purchase object or return a 404 error
    Purchase_instance = get_object_or_404(warehouse_info, id=id)
    
    # Delete the object
    Purchase_instance.delete()
    messages.success(request, 'ریکارد گدام شما موفقانه حذف شد ')
    return redirect('warehouse:warehouse_part')  # Redirect to the main Purchase page


def edit_warehouse(request, id):
    if request.method == "POST":
        
        edit_daily_project_task = warehouse_info.objects.get(pk=id)
        
        edit_daily_project_form = warehouse_infoForm(instance=edit_daily_project_task, data=request.POST)
        if edit_daily_project_form.is_valid():
            edit_daily_project_form.save()
            messages.success(request, ' تغییرات در گدام ذیل موفقانه انجام شد.')
            id = id
            return HttpResponseRedirect(reverse("warehouse:warehouse_part"))
    else:
        id = id
        edit_daily_project_task = warehouse_info.objects.get(pk=id)
        edit_daily_project_form = warehouse_infoForm(instance=edit_daily_project_task)
        context = {
            # 'attendance': attendance,
            'edit_daily_project_form': edit_daily_project_form,
            'id':id,
        }
        return render(request, "product_and_catago/edit_warehouse.html", context)



def transfer_pro_to_godams(request):
    referer = request.META.get('HTTP_REFERER', '/')
    find_all_records = tranfer_products.objects.all()
    if request.method == 'POST':
        form = tranfer_productsForm(request.POST)
        if form.is_valid():
            instace_form = form.save(commit=False)
            source_godam_id = form.cleaned_data.get('source_warehouse')
            find_s_id = source_godam_id.id
            find_s_ware = warehouse_info.objects.get(id=find_s_id)
            to_godam = form.cleaned_data.get('to_warehouse')
            find_to_id = to_godam.id
            find_ware = warehouse_info.objects.get(id=find_to_id)



            product_id = form.cleaned_data.get('product_send')
            p = product_id.id
            find_pro = product.objects.get(id=p)
            

            quantity = form.cleaned_data.get('quantity')
            weight = form.cleaned_data.get('weight')

            find_pro_in = inventrories.objects.filter(warehouse_foerignkey=find_s_id,in_and_out='IN',product_foerignkey=product_id.id).aggregate(
                total_weight_in_Purchase=Sum('weight_field'),
                total_quantity_in_Purchase=Sum('Quantity')
            )
            find_pro_out = inventrories.objects.filter(warehouse_foerignkey=find_s_id,in_and_out='OUT',product_foerignkey=product_id.id).aggregate(
                total_weight_in_sale=Sum('weight_field'),
                total_quantity_in_sale=Sum('Quantity')
            )
            find_exist_amount_weight = (find_pro_in['total_weight_in_Purchase'] or 0) - (find_pro_out['total_weight_in_sale'] or 0)
            find_exist_amount_quantity = (find_pro_in['total_quantity_in_Purchase'] or 0) - (find_pro_out['total_quantity_in_sale'] or 0)

            if quantity > find_exist_amount_quantity or weight > find_exist_amount_weight:
                messages.warning(request,'مقدار موجودی محصول که میخواهید به گدام دیگر ارسال کنید کمتز از موجودی گدام ارسال کننده است ')
                return redirect(referer)
            else:
                form.save()
                inventrories.objects.create(
                    pucrchase_foerignkey=None,
                    product_foerignkey=find_pro,
                    warehouse_foerignkey=find_s_ware,
                    Quantity=quantity,
                    weight_field=weight,
                    in_and_out='OUT'
                )
                inventrories.objects.create(
                    pucrchase_foerignkey=None,
                    product_foerignkey=find_pro,
                    warehouse_foerignkey=find_ware,
                    Quantity=quantity,
                    weight_field=weight,
                    in_and_out='IN'
                )
                
                messages.success(request,'محصول موفقانه انتقال یافت ')
                return redirect(referer)
            
    else:
        form = tranfer_productsForm()
        context = {
            'form':form,
            'find_all_records':find_all_records,
        }
    return render(request,"product_and_catago/trander_pro.html",context)
    