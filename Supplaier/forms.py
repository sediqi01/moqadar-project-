from.models import *
from django import forms
from Customer.models import Customer

from jalali_date.widgets import AdminJalaliDateWidget

class SupplaierForm(forms.ModelForm):
     reg_date = forms.CharField(label='تاریخ',widget=AdminJalaliDateWidget(attrs={"placeholder": "0/0/0000", "id": "datepicker11",'class': 'form-control' }))

     class Meta:
          model = Customer
          fields =  ["reg_date","name","phone","address","detail"]
         
     def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
         
          self.fields["name"].widget.attrs.update(
          {"class": "form-control", "placeholder": "اسم تامین کننده"}
          )

          self.fields["phone"].widget.attrs.update(
          {"class": "form-control", "placeholder": "شماره موبایل"}
          )
          self.fields["address"].widget.attrs.update(
          {"class": "form-control", "placeholder": "آدرس"}
          )
          self.fields["detail"].widget.attrs.update(
          {"class": "form-control", "placeholder": "توضیحات"}
          )