from django.db import models
from django_extensions.db.fields import AutoSlugField
from django.core.exceptions import ValidationError
from django.utils import timezone



from store.models import Item
from accounts.models import Vendor, Customer

DELIVERY_CHOICES = [("P", "Pending"), ("S", "Successful")]


class Sale(models.Model):
    """
    Represents a sale transaction involving a customer.
    """

    date_added = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Sale Date"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.DO_NOTHING,
        db_column="customer"
    )
    sub_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )
    grand_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )
    tax_percentage = models.FloatField(default=0.0)
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )
    amount_change = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0
    )

    class Meta:
        db_table = "sales"
        verbose_name = "Sale"
        verbose_name_plural = "Sales"

    def __str__(self):
        """
        Returns a string representation of the Sale instance.
        """
        return (
            f"Sale ID: {self.id} | "
            f"Grand Total: {self.grand_total} | "
            f"Date: {self.date_added}"
        )

    def sum_products(self):
        """
        Returns the total quantity of products in the sale.
        """
        return sum(detail.quantity for detail in self.saledetail_set.all())


class SaleDetail(models.Model):
    """
    Represents details of a specific sale, including item and quantity.
    """

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        db_column="sale",
        related_name="saledetail_set"
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.DO_NOTHING,
        db_column="item"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    quantity = models.PositiveIntegerField()
    total_detail = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "sale_details"
        verbose_name = "Sale Detail"
        verbose_name_plural = "Sale Details"

    def __str__(self):
        """
        Returns a string representation of the SaleDetail instance.
        """
        return (
            f"Detail ID: {self.id} | "
            f"Sale ID: {self.sale.id} | "
            f"Quantity: {self.quantity}"
        )

class Purchase(models.Model):
    slug = AutoSlugField(
        unique=True,
        populate_from="raw_material_vendor"
    )
    raw_material_vendor = models.ForeignKey(
        'accounts.Vendor',
        on_delete=models.CASCADE,
        db_column='raw_material_vendor_id',
        related_name='purchases'
    )
    date = models.DateField(
        # auto_now_add=True,
        default=timezone.now,
        editable=True, 
        help_text="Date when the purchase was recorded"
    )
    description = models.TextField(
        max_length=300,
        blank=True,
        null=True
    )
    sub_total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    grand_total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    remarks = models.TextField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'purchase'
        ordering = ['date']

    def __str__(self):
        return f"Purchase #{self.pk}"

class PurchaseDetailed(models.Model):
    PURCHASE_TYPE_CHOICES = [
        ('consumable', 'Consumable'),
        ('non-consumable', 'Non‑Consumable'),
    ]

    purchase = models.ForeignKey(
        'transactions.Purchase',
        on_delete=models.CASCADE,
        db_column='purchase_id'
    )
    type = models.CharField(
        max_length=15,
        choices=PURCHASE_TYPE_CHOICES
    )
    expiration_date = models.DateField(null=True, blank=True)

    raw_material = models.ForeignKey(
        'store.RawMaterial',
        on_delete=models.CASCADE,
        db_column='raw_material_id'
    )
    unit_of_measure = models.TextField()
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'purchase_detailed'
        ordering = ['-created_at']

    def __str__(self):
        return f"Detail #{self.pk} for Purchase {self.purchase_id}"

class OtherPurchase(models.Model):
    """
    Represents purchases not tied to specific inventory items.
    """
    source = models.CharField(
        max_length=255, 
        verbose_name="From",
        help_text="Source/origin of the purchase",
        null=False
    )
    date = models.DateTimeField(
        verbose_name="Purchase Date"
    )
    description = models.TextField(
        verbose_name="Purchase Details"
    )
    sub_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Subtotal Amount"
    )
    grand_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Total Amount"
    )
    remarks = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Additional Notes"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Record Creation Date"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Last Updated"
    )

    def __str__(self):
        return f"{self.source} - {self.date.strftime('%Y-%m-%d')}"

    class Meta:
        db_table = 'other_purchase'
        ordering = ['-date']
        verbose_name = 'Non-Inventory Purchase'
        verbose_name_plural = 'Non-Inventory Purchases'

class OtherPurchaseDetailed(models.Model):
    PURCHASE_TYPES = [
        ('stationary', 'Stationary'),
        ('sanitary', 'Sanitary'),
        ('furniture', 'Furniture'),
        ('equipment', 'Equipment'),
        ('other', 'Other'),
    ]

    other_purchase_id = models.ForeignKey(
        OtherPurchase,
        on_delete=models.CASCADE,
        related_name='details'
    )
    unit_of_measure = models.CharField(
        max_length=20,
        choices=[
            ('unit', 'Unit'),
            ('box', 'Box'),
            ('pack', 'Pack'),
            ('set', 'Set'),
            ('kg', 'Kilogram'),
            ('liter', 'Liter')
        ],
        default='unit'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    type = models.CharField(
        max_length=10,
        choices=PURCHASE_TYPES,
        default='other'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Auto-calculate total price before saving"""
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)

 
    def __str__(self):
        return f"{self.get_type_display()} - {self.quantity} {self.get_unit_of_measure_display()}"

    class Meta:
        db_table = 'other_purchase_detailed'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['unit_of_measure']),
        ]
        verbose_name = 'Detailed Non-Inventory Purchase'
        verbose_name_plural = 'Detailed Non-Inventory Purchases'

# offer discount table
class OfferDiscount(models.Model):
    TYPE_CHOICES = [
        ('offer', 'Special Offer'),
        ('discount', 'Discount'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField(verbose_name="Effective Date")
    valid_from = models.DateTimeField()
    valid_till = models.DateTimeField()
    remarks = models.TextField(blank=True, null=True)
    type = models.CharField(
        max_length=8,
        choices=TYPE_CHOICES,
        default='offer',
        verbose_name="Offer/Discount Type"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate date ranges"""
        if self.valid_till <= self.valid_from:
            raise ValidationError("Valid Till date must be after Valid From date")
        
        if self.date > self.valid_from:
            raise ValidationError("Effective date cannot be after validity start")

    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"

    class Meta:
        db_table = 'offer_discount'
        ordering = ['-valid_from']
        verbose_name = 'Offer/Discount'
        verbose_name_plural = 'Offers & Discounts'
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['valid_from', 'valid_till']),
        ]

# offer discount detailed table

class OfferDiscountDetailed(models.Model):
    TYPE_CHOICES = [
        ('offer', 'Offer'),
        ('discount', 'Discount'),
    ]

    type = models.CharField(
        max_length=8,
        choices=TYPE_CHOICES,
        default='offer'
    )
    offer_id = models.ForeignKey(
        'OfferDiscount',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='offer_details'
    )
    discount_id = models.ForeignKey(
        'OfferDiscount',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='discount_details'
    )
    product_id = models.ForeignKey(
        'store.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Related Product'
    )
    vendor_id = models.ForeignKey(
        'accounts.Customer',  # Assuming Vendor model exists in store app
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Related Vendor'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate relationship constraints"""
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_display()} Details - {self.offer or self.discount}"

    class Meta:
        db_table = 'offer_discount_detailed'
        verbose_name = 'Offer/Discount Detail'
        verbose_name_plural = 'Offer/Discount Details'
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['offer_id', 'discount_id']),
        ]