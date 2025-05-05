from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Category, Item, Batch

class StoreTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Creating a test user
        cls.user = User.objects.create_user(username='testuser', password='testpass123')
        
    def test_category_creation(self):
        cat = Category.objects.create(name="DolpoClassic")
        self.assertEqual(str(cat), "Category: DolpoClassic")

    def test_item_creation(self):
        cat = Category.objects.create(name="Popsicles")
        item = Item.objects.create(
            name="FlavouredPopsicle", 
            category=cat,
            selling_price=2.50,
            quantity=100
        )
        self.assertIn("FlavouredPopsicle", str(item))

    # def test_zero_quantity_validation(self):
    #     with self.assertRaises(ValidationError):
    #         Item.objects.create(..., quantity=-5)

    def test_zero_quantity_validation(self):
        cat = Category.objects.create(name="Test Category")
        with self.assertRaises(ValidationError):
            item = Item(
                name="Test Product",
                category=cat,
                selling_price=10.00,
                quantity=-5  # Invalid negative quantity
            )
            item.full_clean()  # Explicit validation call

    def test_product_list_view(self):
        # Log in the user first
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('productslist'))  # Make sure this URL name matches your actual URL
        self.assertEqual(response.status_code, 200)

    