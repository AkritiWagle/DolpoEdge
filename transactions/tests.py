from django.test import TestCase
from store.models import Item
from accounts.models import Customer,Vendor
from .models import Sale, Purchase

class TransactionTests(TestCase):

    def test_sale_creation(self):
        customer = Customer.objects.create(name="Test Customer")
        sale = Sale.objects.create(customer=customer, grand_total=100.00)
        self.assertIn(f"Sale ID: {sale.id}", str(sale))

    def test_purchase_str(self):
        vendor = Vendor.objects.create(name="Raw Mat Ltd")
        purchase = Purchase.objects.create(
            raw_material_vendor=vendor, 
            grand_total=100.00, 
            sub_total=100.00
            )

        self.assertIn("Purchase #", str(purchase))