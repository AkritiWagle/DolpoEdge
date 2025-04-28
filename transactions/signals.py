from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import PurchaseDetailed

@receiver(pre_save, sender=PurchaseDetailed,
          dispatch_uid="transactions_purchase_detailed_track_quantity_change")
def track_quantity_change(sender, instance, **kwargs):
    try:
        instance._old_quantity = sender.objects.get(pk=instance.pk).quantity
    except sender.DoesNotExist:
        instance._old_quantity = 0

@receiver(post_save, sender=PurchaseDetailed,
          dispatch_uid="transactions_purchase_detailed_update_inventory")
def update_raw_material_inventory(sender, instance, created, **kwargs):
    raw_material = instance.raw_material
    if created:
        raw_material.quantity += instance.quantity
    else:
        diff = instance.quantity - getattr(instance, "_old_quantity", 0)
        raw_material.quantity += diff
    if instance.expiration_date:
        raw_material.expiration_date = instance.expiration_date
    raw_material.save()
