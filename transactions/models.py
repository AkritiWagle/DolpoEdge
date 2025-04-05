from django.db import models
from django_extensions.db.fields import AutoSlugField
from django.core.exceptions import ValidationError


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
    """
    Represents a purchase of an item,
    including vendor details and delivery status.
    """

    slug = AutoSlugField(unique=True, populate_from="vendor")
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    description = models.TextField(max_length=300, blank=True, null=True)
    vendor = models.ForeignKey(
        Vendor, related_name="purchases", on_delete=models.CASCADE
    )
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField(
        blank=True, null=True, verbose_name="Delivery Date"
    )
    quantity = models.PositiveIntegerField(default=0)
    delivery_status = models.CharField(
        choices=DELIVERY_CHOICES,
        max_length=1,
        default="P",
        verbose_name="Delivery Status",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        verbose_name="Price per item (Ksh)",
    )
    total_value = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        """
        Calculates the total value before saving the Purchase instance.
        """
        self.total_value = self.price * self.quantity
        super().save(*args, **kwargs)
        # Update the item quantity
        self.item.quantity += self.quantity
        self.item.save()

    def __str__(self):
        """
        Returns a string representation of the Purchase instance.
        """
        return str(self.item.name)

    class Meta:
        ordering = ["order_date"]


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

    # def clean(self):
    #     """Validation for pricing consistency"""
    #     if self.total_price != self.unit_price * self.quantity:
    #         raise ValidationError("Total price must equal unit price × quantity")

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
        # errors = {}
        
        # # Ensure only one of offer/discount is set based on type
        # if self.type == 'offer' and not self.offer:
        #     errors['offer'] = 'Offer must be set for offer type'
        # if self.type == 'discount' and not self.discount:
        #     errors['discount'] = 'Discount must be set for discount type'
        # if self.offer and self.discount:
        #     errors['offer'] = 'Cannot have both offer and discount references'
            
        # if errors:
        #     raise ValidationError(errors)

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