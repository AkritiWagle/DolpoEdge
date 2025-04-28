from django import forms

from accounts.models import Vendor
from store.models import RawMaterial
from .models import Purchase, PurchaseDetailed


class BootstrapMixin(forms.ModelForm):
    """
    A mixin to add Bootstrap classes to form fields.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


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