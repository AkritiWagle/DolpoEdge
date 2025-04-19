from django import forms
from .models import Purchase


class BootstrapMixin(forms.ModelForm):
    """
    A mixin to add Bootstrap classes to form fields.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


# class PurchaseForm(BootstrapMixin, forms.ModelForm):
#     """
#     A form for creating and updating Purchase instances.
#     """
#     class Meta:
#         model = Purchase
#         fields = [
#             'item',  'price', 'description', 'vendor',
#             'quantity', 'delivery_date', 'delivery_status'
#         ]
#         widgets = {
#             'delivery_date': forms.DateInput(
#                 attrs={
#                     'class': 'form-control',
#                     'type': 'datetime-local'
#                 }
#             ),
#             'description': forms.Textarea(
#                 attrs={'rows': 1, 'cols': 40}
#             ),
#             'quantity': forms.NumberInput(
#                 attrs={'class': 'form-control'}
#             ),
#             'delivery_status': forms.Select(
#                 attrs={'class': 'form-control'}
#             ),
#             'price': forms.NumberInput(
#                 attrs={'class': 'form-control'}
#             ),
#         }

class PurchaseForm(forms.ModelForm):
    """
    A form for creating and updating Purchase instances
    with only the desired fields.
    """
    class Meta:
        model = Purchase
        fields = [
            'raw_material_vendor',
            'date',
            'description',
            'sub_total',
            'grand_total',
            'remarks',
        ]
        widgets = {
            # ForeignKey → <select>
            'raw_material_vendor': forms.Select(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Choose a vendor',
                }
            ),
            # HTML5 date picker
            'date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            # Free‑form text
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Optional description'
                }
            ),
            # Decimal fields with step for cents
            'sub_total': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01'
                }
            ),
            'grand_total': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01'
                }
            ),
            # Optional remarks
            'remarks': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Optional remarks'
                }
            ),
        }