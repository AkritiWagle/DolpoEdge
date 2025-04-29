from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from accounts.models import Vendor, Customer
from store.models import RawMaterial
from .models import Purchase, PurchaseDetailed, SalesReport, PurchaseReport


class BootstrapMixin(forms.ModelForm):
    """
    A mixin to add Bootstrap classes to form fields.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

class BaseReportForm(forms.Form):
    TIME_FRAMES = [
        ('custom', 'Custom Dates'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Biweekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    time_frame = forms.ChoiceField(choices=TIME_FRAMES)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

class SalesReportForm(forms.ModelForm):
    class Meta:
        model = SalesReport
        fields = ['name', 'report_type', 'time_frame', 'start_date', 'end_date', 'customer']
        widgets = {
            'time_frame': forms.HiddenInput(),  # Add this

            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'customer': forms.Select(attrs={'class': 'select2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all()
        self.fields['customer'].required = False

        if self.initial.get('report_type') == 'all' or self.data.get('report_type') == 'all':
            self.fields['customer'].disabled = True
            self.fields['customer'].widget.attrs['disabled'] = True
            self.fields['customer'].widget.attrs['data-previous-value'] = ''

    def clean(self):
        cleaned_data = super().clean()
        report_type = cleaned_data.get('report_type')
        customer = cleaned_data.get('customer')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
             self.add_error('end_date', "End date must be after start date")

        if report_type == 'customer' and not customer:
            raise ValidationError("Customer is required when selecting 'Single Customer' report type")
            
        if report_type == 'all' and customer:
            cleaned_data['customer'] = None  # Force reset customer

        return cleaned_data


class PurchaseReportForm(forms.ModelForm):
    class Meta:
        model = PurchaseReport
        fields = ['name', 'report_type', 'purchase_type', 'time_frame', 'start_date', 'end_date', 'vendor']
        widgets = {
            'time_frame': forms.HiddenInput(),  # Add this

            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'vendor': forms.Select(attrs={'class': 'select2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vendor'].queryset = Vendor.objects.all()
        self.fields['vendor'].required = False

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                self.add_error('end_date', "End date must be after start date")
                
        return cleaned_data


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['raw_material_vendor', 'date', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_date'
            }),
            'raw_material_vendor': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_raw_material_vendor'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'id': 'id_remarks'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['raw_material_vendor'].queryset = Vendor.objects.all()
        self.fields['raw_material_vendor'].empty_label = "Select Vendor"

class PurchaseItemForm(forms.ModelForm):
    expiration_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )

    class Meta:
        model = PurchaseDetailed
        fields = ['raw_material', 'quantity', 'unit_price']
        widgets = {
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['raw_material'].queryset = RawMaterial.objects.all()