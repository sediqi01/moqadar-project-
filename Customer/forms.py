from.models import *
from django import forms
from jalali_date.widgets import AdminJalaliDateWidget


class CustomerForm(forms.ModelForm):
     reg_date = forms.CharField(label='تاریخ',widget=AdminJalaliDateWidget(attrs={"placeholder": "0/0/0000", "id": "datepicker10",'class': 'form-control' }))
     class Meta:
          model = Customer
          fields =  ["name","phone","address","detail","reg_date"]
         
     def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
         
          
          self.fields["name"].widget.attrs.update(
          {"class": "form-control", "placeholder": "نام مشتری را بنویسید"}
          )
          self.fields["phone"].widget.attrs.update(
          {"class": "form-control", "placeholder": "شماره تماس مشتری را بنویسید "}
          )
          self.fields["address"].widget.attrs.update(
          {"class": "form-control", "placeholder": "آدرس مشتری را بنویسید"}
          )
          self.fields["detail"].widget.attrs.update(
          {"class": "form-control", "placeholder": "معلومات اضافی در مورد مشتری را بنویسید (اختیاری)"}
          )


class LoanForm(forms.ModelForm):
     date_issued = forms.CharField(label='تاریخ',widget=AdminJalaliDateWidget(attrs={"placeholder": "0/0/0000", "id": "datepicker13",'class': 'form-control' }))
     class Meta:
          model = Loan
          fields = ["amount", "date_issued", "notes"]

     def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)

          self.fields["amount"].widget.attrs.update(
               {"class": "form-control", "placeholder": "مقدار پول را وارد کنید؟"}
          )
        
          self.fields["notes"].widget.attrs.update(
               {"class": "form-control", "placeholder": "توضیحات اضافی"}
          )

from Order.models import sale_item_part
from django.forms.widgets import CheckboxSelectMultiple



class LoansaleForm(forms.ModelForm):
     date_issued = forms.CharField(label='تاریخ',widget=AdminJalaliDateWidget(attrs={"placeholder": "0/0/0000", "id": "datepicker14",'class': 'form-control' }))
     sale_id_for_pay = forms.ModelMultipleChoiceField(
          queryset=sale_item_part.objects.none(),
          widget=forms.SelectMultiple(attrs={"class": "form-control select2", "multiple": "multiple"}),
          required=False
     )
     class Meta: 
          model = Loan
          fields = ["amount", "date_issued", "sale_id_for_pay","notes"] 
     def __init__(self, *args, customer_id=None, **kwargs):
          super().__init__(*args, **kwargs)

          self.fields["amount"].widget.attrs.update(
               {"class": "form-control", "placeholder": "مقدار پول را وارد کنید؟"}
          )
         
          self.fields["notes"].widget.attrs.update(
               {"class": "form-control", "placeholder": "توضیحات اضافی"}
          )
          if customer_id:
            self.fields['sale_id_for_pay'].queryset = sale_item_part.objects.filter(
                sell_forei__customer_id=customer_id,is_money_approved=False
            )
            self.fields['sale_id_for_pay'].label_from_instance = lambda obj: f"فروش {obj.id} -  مقدار باقی: {obj.borrow_amount} افغانی"
        
        


class SLoanForm(forms.ModelForm):
     date_issued = forms.CharField(label='تاریخ',widget=AdminJalaliDateWidget(attrs={"placeholder": "0/0/0000", "id": "datepicker12",'class': 'form-control' }))
     class Meta:
          model = SLoan
          fields = ["amount", "date_issued", "notes"]

     def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)

          self.fields["amount"].widget.attrs.update(
               {"class": "form-control", "placeholder": "مقدار پول را وارد کنید؟"}
          )
         
          self.fields["notes"].widget.attrs.update(
               {"class": "form-control", "placeholder": "توضیحات اضافی"}
          )
        

from purchase.models import BothPartyLedger
class bothpartyForm(forms.ModelForm):
     date_is = forms.CharField(label='تاریخ',widget=AdminJalaliDateWidget(attrs={"placeholder": "0/0/0000", "id": "datepicker13",'class': 'form-control' }))
     class Meta:
          model = BothPartyLedger
          fields = ["date_is"]
     def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
