"""
Module: models.py

Contains Django models for handling categories, items, and deliveries.

This module defines the following classes:
- Category: Represents a category for items.
- Item: Represents an item in the inventory.
- Delivery: Represents a delivery of an item to a customer.

Each class provides specific fields and methods for handling related data.
"""

from datetime import timezone
from django.db import models
from django.urls import reverse
from django.forms import model_to_dict
from django_extensions.db.fields import AutoSlugField
from phonenumber_field.modelfields import PhoneNumberField
from accounts.models import Vendor
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model




class Category(models.Model):
    """
    Represents a category for items.
    """
    name = models.CharField(max_length=255)
    slug = AutoSlugField(unique=True, populate_from='name')
    remarks = models.TextField(null=True, blank=True, help_text="Additional notes about the category")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        String representation of the category.
        """
        return f"Category: {self.name}"

    class Meta:
        verbose_name_plural = 'Categories'
        db_table = 'categories'


class Item(models.Model):
    """
    Represents an item in the inventory.
    """
    slug = AutoSlugField(unique=True, populate_from='name')
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=256)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    validators=[MinValueValidator(0)]
    # price = models.FloatField(default=0)
    selling_price = models.FloatField(default=0, verbose_name='Selling Price')

    # vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        String representation of the item.
        """
        return (
            f"{self.name} - Category: {self.category}, "
            f"Quantity: {self.quantity}"
        )

    def get_absolute_url(self):
        """
        Returns the absolute URL for an item detail view.
        """
        return reverse('item-detail', kwargs={'slug': self.slug})

    def to_json(self):
        product = model_to_dict(self)
        product['id'] = self.id
        product['text'] = self.name
        product['category'] = self.category.name
        product['quantity'] = 1
        product['total_product'] = 0
        return product

    class Meta:
        db_table = 'product'
        ordering = ['name']
        verbose_name_plural = 'Items'

class Batch(models.Model):
    """
    Represents a batch of products with manufacturing/expiration tracking.
    """
    name = models.CharField(max_length=255, unique=True)
    manufacturing_date = models.DateTimeField()
    expiration_date = models.DateTimeField()
    quantity = models.IntegerField(default=0)
    product = models.ForeignKey(
        Item, 
        on_delete=models.CASCADE,
        related_name='batches'
    )
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Batch {self.name} - {self.product.name}"

    def clean(self):
        """Validation logic for date consistency"""
        super().clean()
        
        if self.expiration_date <= self.manufacturing_date:
            raise ValidationError({
                'expiration_date': 'Expiration date must be after manufacturing date'
            })

    def save(self, *args, **kwargs):
        """Ensure validations are run on every save"""
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'batch'
        verbose_name_plural = 'Batches'
        ordering = ['-manufacturing_date']
        indexes = [
            models.Index(fields=['manufacturing_date'], name='manufacturing_date_idx'),
            models.Index(fields=['expiration_date'], name='expiration_date_idx'),
            models.Index(fields=['product', 'manufacturing_date'], name='product_manufacturing_idx'),
        ]

class RawMaterial(models.Model):
    """
    Represents raw materials inventory with vendor tracking.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    expiration_date = models.DateTimeField(blank=True, null=True)
    unit_of_measure = models.CharField(max_length=20)
    quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    remarks = models.TextField(blank=True, null=True)
    vendor = models.ForeignKey(
        'accounts.Vendor',  # Cross-app reference
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Supplier'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'raw_material'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit_of_measure})"
class BaseRecipe(models.Model):
    name = models.CharField(max_length=255, unique=True)
    final_product_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(BaseRecipe, on_delete=models.CASCADE, related_name='ingredients')
    raw_material = models.ForeignKey('RawMaterial', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Store unit of measure at time of recipe creation
    unit_of_measure = models.CharField(max_length=20)

    class Meta:
        unique_together = ('recipe', 'raw_material')

    def __str__(self):
        return f"{self.raw_material.name} - {self.quantity} {self.unit_of_measure}"

class Insight(models.Model):
    INSIGHT_TYPE_CHOICES = [
        ('sales_trend', 'Sales Trend'),
        ('top_selling', 'Top Selling'),
        ('vendor_performance', 'Vendor Performance'),
        ('other', 'Other'),
    ]
    
    insight_type = models.CharField(
        max_length=20,
        choices=INSIGHT_TYPE_CHOICES,
        default='other'
    )
    related_entity_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ['item', 'vendor']},
    )
    related_entity_id = models.PositiveIntegerField()
    related_entity = GenericForeignKey('related_entity_type', 'related_entity_id')
    metric = models.CharField(max_length=255)
    value = models.FloatField()
    calculated_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)

    def clean(self):
        # Validate entity type matches allowed models
        if self.related_entity_type.model not in ['item', 'vendor']:
            raise ValidationError("Related entity must be an Item or Vendor.")
        
        # Validate insight-type and entity compatibility
        if self.insight_type == 'vendor_performance' and self.related_entity_type.model != 'vendor':
            raise ValidationError("Vendor insights must link to a Vendor.")
        if self.insight_type == 'top_selling' and self.related_entity_type.model != 'item':
            raise ValidationError("Top Selling insights must link to a Product.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Create an alert for this insight
        Alerts.objects.create(
            alert_type='insight',  # Requires adding 'insight' to Alerts.ALERT_TYPES
            related_item_type=self.related_entity_type.model,
            content_type=self.related_entity_type,
            object_id=self.related_entity_id,
            description=f"Insight: {self.get_insight_type_display()} ({self.metric}={self.value})",
            priority='notice',
            status='pending'
        )

    def __str__(self):
        return f"{self.insight_type} - {self.metric}"

    class Meta:
        db_table = 'insights'
        ordering = ['-calculated_date']


#operations inventory table

class OperationsInventory(models.Model):
    TYPE_CHOICES = [
        ('packaging', 'Packaging Material'),
        ('other', 'Other Operational Item'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='packaging'
    )
    unit_of_measure = models.CharField(max_length=20)
    quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    vendor = models.ForeignKey(
        'accounts.Vendor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Supplier'
    )
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validate inventory values"""
        if self.quantity < 0:
            raise ValidationError("Quantity cannot be negative")
        if self.unit_price < 0:
            raise ValidationError("Unit price cannot be negative")

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit_of_measure})"

    class Meta:
        db_table = 'operations_inventory'
        verbose_name = 'Operations Inventory'
        verbose_name_plural = 'Operations Inventories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['vendor']),
        ]

#Stock table

class Stock(models.Model):
    STOCK_TYPE_CHOICES = [
        ('product', 'Product Stock'),
        ('raw_material', 'Raw Material Stock'),
        ('operations', 'Operations Stock'),
    ]

    # Common fields
    quantity = models.IntegerField(default=0)
    unit_of_measure = models.CharField(max_length=20)
    last_updated = models.DateTimeField(auto_now=True)
    stock_type = models.CharField(
        max_length=13,
        choices=STOCK_TYPE_CHOICES,
        default='product'
    )
    
    # Batch relationship
    batch = models.ForeignKey(
        'Batch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Generic foreign key for different item types
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            'model__in': ['item', 'rawmaterial', 'operationsinventory']
        }
    )
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')

    # Common metadata
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)

    def clean(self):
        """Validate stock type matches content type"""
        type_model_map = {
            'product': 'item',
            'raw_material': 'rawmaterial',
            'operations': 'operationsinventory'
        }
        
        expected_model = type_model_map.get(self.stock_type)
        if self.content_type.model != expected_model:
            raise ValidationError(
                f"Stock type {self.stock_type} requires {expected_model} model"
            )

        if self.quantity < 0:
            raise ValidationError("Quantity cannot be negative")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_stock_type_display()} Stock - {self.item}"

    class Meta:
        db_table = 'stock'
        verbose_name = 'Unified Stock'
        verbose_name_plural = 'Unified Stock'
        indexes = [
            models.Index(fields=['stock_type']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    @property
    def get_stock_item_display(self):
        """Returns the actual stock item instance"""
        return self.item

#alerts table
class Alerts(models.Model):
    ALERT_TYPES = [
        ('low_stock', 'Low Stock Alert'),
        ('expiration', 'Expiration Alert'),
    ]
    
    ITEM_TYPES = [
        ('product', 'Product'),
        ('raw_material', 'Raw Material'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
    ]

    PRIORITY_CHOICES = [
        ('critical', 'Critical'),
        ('warning', 'Warning'),
        ('notice', 'Notice'),
    ]

    alert_type = models.CharField(
        max_length=10,
        choices=ALERT_TYPES,
        default='low_stock'
    )
    related_item_type = models.CharField(
        max_length=13,
        choices=ITEM_TYPES,
        default='product'
    )
    priority = models.CharField(
        max_length=8,
        choices=PRIORITY_CHOICES,
        default='notice',
        help_text="Severity level osf the alert"
    )
    
    # Generic foreign key setup
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ['item', 'rawmaterial']}
    )
    object_id = models.PositiveIntegerField()
    related_item = GenericForeignKey('content_type', 'object_id')
    
    description = models.TextField()
    date_generated = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=8,
        choices=STATUS_CHOICES,
        default='pending'
    )
    resolved_date = models.DateTimeField(null=True, blank=True)

    def clean(self):
        # Validate item type matches content type
        type_model_map = {
            'product': 'item',
            'raw_material': 'rawmaterial'
        }
        
        expected_model = type_model_map.get(self.related_item_type)
        if self.content_type.model != expected_model:
            raise ValidationError(
                f"Item type {self.related_item_type} requires {expected_model} model"
            )
            
        # Validate resolution status
        if self.status == 'resolved' and not self.resolved_date:
            raise ValidationError("Resolved date is required when status is resolved")
            
        if self.resolved_date and self.status != 'resolved':
            raise ValidationError("Status must be resolved when resolved date is set")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.related_item} ({self.status})"

    class Meta:
        db_table = 'alerts'
        verbose_name = 'Inventory Alert'
        verbose_name_plural = 'Inventory Alerts'
        indexes = [
            models.Index(fields=['alert_type']),
            models.Index(fields=['status']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    @property
    def alert_age(self):
        """Returns days since alert was generated"""
        if self.status == 'resolved':
            return (self.resolved_date - self.date_generated).days
        return (timezone.now() - self.date_generated).days


class Delivery(models.Model):
    """
    Represents a delivery of an item to a customer.
    """
    item = models.ForeignKey(
        Item, blank=True, null=True, on_delete=models.SET_NULL
    )
    customer_name = models.CharField(max_length=30, blank=True, null=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    location = models.CharField(max_length=20, blank=True, null=True)
    date = models.DateTimeField()
    is_delivered = models.BooleanField(
        default=False, verbose_name='Is Delivered'
    )

    def __str__(self):
        """
        String representation of the delivery.
        """
        return (
            f"Delivery of {self.item} to {self.customer_name} "
            f"at {self.location} on {self.date}"
        )
