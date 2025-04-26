from django import forms

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


# class PurchaseForm(forms.ModelForm):
#     """
#     A form for creating and updating Purchase instances
#     with only the desired fields.
#     """
#     class Meta:
#         model = Purchase
#         fields = [
#             'raw_material_vendor',
#             'date',
#             'description',
#             'sub_total',
#             'grand_total',
#             'remarks',
#         ]
#         widgets = {
#             # ForeignKey → <select>
#             'raw_material_vendor': forms.Select(
#                 attrs={
#                     'class': 'form-control',
#                     'placeholder': 'Choose a vendor',
#                 }
#             ),
#             # HTML5 date picker
#             'date': forms.DateInput(
#                 attrs={
#                     'class': 'form-control',
#                     'type': 'date'
#                 }
#             ),
#             # Free‑form text
#             'description': forms.Textarea(
#                 attrs={
#                     'class': 'form-control',
#                     'rows': 2,
#                     'placeholder': 'Optional description'
#                 }
#             ),
#             # Decimal fields with step for cents
#             'sub_total': forms.NumberInput(
#                 attrs={
#                     'class': 'form-control',
#                     'step': '0.01'
#                 }
#             ),
#             'grand_total': forms.NumberInput(
#                 attrs={
#                     'class': 'form-control',
#                     'step': '0.01'
#                 }
#             ),
#             # Optional remarks
#             'remarks': forms.Textarea(
#                 attrs={
#                     'class': 'form-control',
#                     'rows': 2,
#                     'placeholder': 'Optional remarks'
#                 }
#             ),
#         }

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['raw_material_vendor', 'date', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

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