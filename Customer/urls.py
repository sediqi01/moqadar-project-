from django.urls import path
from . import views



app_name ='Customer'

urlpatterns = [


    path('customer', views.customer, name='customer'),
    path('customer/<slug:slug>/orders/', views.customer_order_detail, name='customer_order_detail'),
    path('customer_full_info/<int:id>/', views.customer_full_info, name='customer_full_info'),
    path('delete/<int:customer_id>/', views.delete_customer, name='delete_customer'),
    path('edit/<int:id>/', views.edit_customer, name='edit_customer'),
    path('customer_loans/<int:id>/', views.customer_loans, name='customer_loans'),
    path('paind_customer_loans/<int:id>/', views.paid_customer_loans, name='paind_customer_loans'),
    path('customer_paid_loans/<int:id>/', views.customer_paid_loans, name='customer_paid_loans'),
    path('paid_with_sale/<int:id>/', views.paid_with_sale, name='paid_with_sale'),
    path('delete_paid_record_od_cudtomer/<int:id>/', views.delete_paid_record_od_cudtomer, name='delete_paid_record_od_cudtomer'),
    path('loan_people/', views.loan_people, name='loan_people'),
    path('both_partner_calculation/<int:id>/', views.both_partner_calculation, name='both_partner_calculation'),
    path('loan-people/print/',  views.loan_people_print, name='loan_people_print'),
    path('delete_both_party_operation/<int:id>/',views.delete_both_party_operation,name='delete_both_party_operation'),
    path(
        'both_partner_calculation/print/<int:id>/',
        views.both_partner_calculation_print,
        name='both_partner_calculation_print'
    ),
    
    
    







]
