from django.test import TestCase
from django.contrib.auth.models import User
from .models import Profile, Vendor, Customer

class AccountsTests(TestCase):
    def test_profile_creation(self):
        # Create user (signal may auto-create profile)
        user = User.objects.create_user(username='test1', password='testpass1')
        
        # Get existing profile instead of creating new
        profile = Profile.objects.get(user=user)
        profile.email = 'test1@example.com'
        profile.save()
        
        self.assertEqual(profile.email, 'test1@example.com')

    def test_vendor_str(self):
        vendor = Vendor.objects.create(name="ABC Supplies")
        self.assertEqual(str(vendor), "ABC Supplies")

    def test_customer_creation(self):
        customer = Customer.objects.create(name="John Doe")
        self.assertEqual(customer.store_type, 'retail')