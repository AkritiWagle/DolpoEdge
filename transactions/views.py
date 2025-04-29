# Standard library imports
from decimal import Decimal
import json
import logging

# Django core imports
from django.http import JsonResponse, HttpResponse
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, render
from django.db import transaction
from django.contrib import messages
from django.core.exceptions import ValidationError



# Class-based views
from django.views.generic import DetailView, ListView, CreateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_http_methods


# Authentication and permissions
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Third-party packages
from openpyxl import Workbook

# Local app imports
from store.models import Item,RawMaterial, Batch,OperationsInventory
from accounts.models import Customer, Vendor
from .models import PurchaseDetailed, Sale, Purchase, SaleDetail, OtherPurchase, OtherPurchaseDetailed
from .forms import PurchaseForm


logger = logging.getLogger(__name__)


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def export_sales_to_excel(request):
    # Create a workbook and select the active worksheet.
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Sales'

    # Define the column headers
    columns = [
        'ID', 'Date', 'Customer', 'Sub Total',
        'Grand Total', 'Tax Amount', 'Tax Percentage',
        'Amount Paid', 'Amount Change'
    ]
    worksheet.append(columns)

    # Fetch sales data
    sales = Sale.objects.all()

    for sale in sales:
        # Convert timezone-aware datetime to naive datetime
        if sale.date_added.tzinfo is not None:
            date_added = sale.date_added.replace(tzinfo=None)
        else:
            date_added = sale.date_added

        worksheet.append([
            sale.id,
            date_added,
            sale.customer.phone,
            sale.sub_total,
            sale.grand_total,
            sale.tax_amount,
            sale.tax_percentage,
            sale.amount_paid,
            sale.amount_change
        ])

    # Set up the response to send the file
    response = HttpResponse(
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    )
    response['Content-Disposition'] = 'attachment; filename=sales.xlsx'
    workbook.save(response)

    return response


def export_purchases_to_excel(request):
    # Create a workbook and select the active worksheet.
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Purchases'

    # Define the column headers
    columns = [
        'ID', 'Item', 'Description', 'Vendor', 'Order Date',
        'Delivery Date', 'Quantity', 'Delivery Status',
        'Price per item (NPR)', 'Total Value'
    ]
    worksheet.append(columns)

    # Fetch purchases data
    purchases = Purchase.objects.all()

    for purchase in purchases:
        # Convert timezone-aware datetime to naive datetime
        delivery_tzinfo = purchase.delivery_date.tzinfo
        order_tzinfo = purchase.order_date.tzinfo

        if delivery_tzinfo or order_tzinfo is not None:
            delivery_date = purchase.delivery_date.replace(tzinfo=None)
            order_date = purchase.order_date.replace(tzinfo=None)
        else:
            delivery_date = purchase.delivery_date
            order_date = purchase.order_date
        worksheet.append([
            purchase.id,
            purchase.item.name,
            purchase.description,
            purchase.vendor.name,
            order_date,
            delivery_date,
            purchase.quantity,
            purchase.get_delivery_status_display(),
            purchase.selling_price,
            purchase.total_value
        ])

    # Set up the response to send the file
    response = HttpResponse(
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    )
    response['Content-Disposition'] = 'attachment; filename=purchases.xlsx'
    workbook.save(response)

    return response

@require_http_methods(["GET"])
def get_raw_materials(request):
    search = request.GET.get('q', '')
    materials = RawMaterial.objects.filter(name__icontains=search)[:10]
    results = [{
        'id': m.id,
        'text': m.name,
        'uom': m.unit_of_measure,
        'unit_price': str(m.unit_price),
        'stock': m.quantity
    } for m in materials]
    return JsonResponse(results, safe=False)

class SaleListView(LoginRequiredMixin, ListView):
    """
    View to list all sales with pagination.
    """

    model = Sale
    template_name = "transactions/sales_list.html"
    context_object_name = "sales"
    paginate_by = 10
    ordering = ['-id']


class SaleDetailView(LoginRequiredMixin, DetailView):
    """
    View to display details of a specific sale.
    """

    model = Sale
    template_name = "transactions/saledetail.html"


def SaleCreateView(request):
    context = {
        "active_icon": "sales",
        "customers": [c.to_select2() for c in Customer.objects.all()]
    }

    if request.method == 'POST':
        if is_ajax(request=request):
            try:
                # Load the JSON data from the request body
                data = json.loads(request.body)
                logger.info(f"Received data: {data}")

                # Validate required fields
                required_fields = [
                    'customer', 'sub_total', 'grand_total',
                    'amount_paid', 'amount_change', 'items'
                ]
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"Missing required field: {field}")

                # Create sale attributes
                sale_attributes = {
                    "customer": Customer.objects.get(id=int(data['customer'])),
                    "sub_total": float(data["sub_total"]),
                    "grand_total": float(data["grand_total"]),
                    "tax_amount": float(data.get("tax_amount", 0.0)),
                    "tax_percentage": float(data.get("tax_percentage", 0.0)),
                    "amount_paid": float(data["amount_paid"]),
                    "amount_change": float(data["amount_change"]),
                }

                # Use a transaction to ensure atomicity
                with transaction.atomic():
                    # Create the sale
                    new_sale = Sale.objects.create(**sale_attributes)
                    logger.info(f"Sale created: {new_sale}")

                    # Create sale details and update item quantities
                    items = data["items"]
                    if not isinstance(items, list):
                        raise ValueError("Items should be a list")

                    for item in items:
                        if not all(
                            k in item for k in [
                                "id", "selling_price", "quantity", "total_item"
                            ]
                        ):
                            raise ValueError("Item is missing required fields")

                        item_instance = Item.objects.get(id=int(item["id"]))
                        if item_instance.quantity < int(item["quantity"]):
                            raise ValueError(f"Not enough stock for item: {item_instance.name}")

                        detail_attributes = {
                            "sale": new_sale,
                            "item": item_instance,
                            "price": float(item["selling_price"]),
                            "quantity": int(item["quantity"]),
                            "total_detail": float(item["total_item"])
                        }
                        SaleDetail.objects.create(**detail_attributes)
                        logger.info(f"Sale detail created: {detail_attributes}")

                        # Reduce item quantity
                        item_instance.quantity -= int(item["quantity"])
                        item_instance.save()

                return JsonResponse(
                    {
                        'status': 'success',
                        'message': 'Sale created successfully!',
                        'redirect': '/transactions/sales/'
                    }
                )

            except json.JSONDecodeError:
                return JsonResponse(
                    {
                        'status': 'error',
                        'message': 'Invalid JSON format in request body!'
                    }, status=400)
            except Customer.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Customer does not exist!'
                    }, status=400)
            except Item.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Item does not exist!'
                    }, status=400)
            except ValueError as ve:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Value error: {str(ve)}'
                    }, status=400)
            except TypeError as te:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Type error: {str(te)}'
                    }, status=400)
            except Exception as e:
                logger.error(f"Exception during sale creation: {e}")
                return JsonResponse(
                    {
                        'status': 'error',
                        'message': (
                            f'There was an error during the creation: {str(e)}'
                        )
                    }, status=500)

    return render(request, "transactions/sale_create.html", context=context)


class SaleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View to delete a sale.
    """

    model = Sale
    template_name = "transactions/saledelete.html"

    def get_success_url(self):
        """
        Redirect to the sales list after successful deletion.
        """
        return reverse("saleslist")

    def test_func(self):
        """
        Allow deletion only for superusers.
        """
        return self.request.user.is_superuser


class PurchaseListView(LoginRequiredMixin, ListView):
    """
    View to list all purchases with pagination.
    """

    model = Purchase
    template_name = "transactions/purchases_list.html"
    context_object_name = "purchases"
    paginate_by = 10
    ordering = ['-id']



class PurchaseDetailView(LoginRequiredMixin, DetailView):
    """
    View to display details of a specific purchase.
    """

    model = Purchase
    template_name = "transactions/purchasedetail.html"


def PurchaseCreateView(request):
    context = {
        "active_icon": "purchases",
        "vendors": Vendor.objects.all(),
        "form": PurchaseForm()
    }

    if request.method == 'POST':
        if is_ajax(request):
            try:
                data = json.loads(request.body)
                logger.info(f"Received purchase data: {data}")

                # Validate required fields
                required_fields = ['raw_material_vendor', 'date', 'items']
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"Missing required field: {field}")

                with transaction.atomic():
                    # Create Purchase
                    purchase = Purchase.objects.create(
                        raw_material_vendor_id=data['raw_material_vendor'],
                        date=data['date'],
                        remarks=data.get('remarks', ''),
                        sub_total=Decimal(data.get('sub_total', 0)),
                        grand_total=Decimal(data.get('grand_total', 0))
                    )

                    # Process items
                    for item in data['items']:
                        raw_material = RawMaterial.objects.get(id=item['id'])
                        
                        # Create PurchaseDetailed entry
                        PurchaseDetailed.objects.create(
                            purchase=purchase,
                            type='consumable',  # Set default or get from frontend
                            raw_material=raw_material,
                            unit_of_measure=raw_material.unit_of_measure,
                            unit_price=Decimal(item['unit_price']),
                            quantity=item['quantity'],
                            total_price=Decimal(item['unit_price']) * item['quantity'],
                        )
                    # Auto-generate description
                    purchase.update_description()

                return JsonResponse({
                    'status': 'success',
                    'message': 'Purchase created successfully!',
                    'redirect': '/transactions/purchases/'
                })

            except RawMaterial.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'One or more raw materials not found'}, status=400)
            except Exception as e:
                logger.error(f"Error creating purchase: {str(e)}", exc_info=True)
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return render(request, "transactions/purchase_create.html", context=context)

class PurchaseUpdateView(LoginRequiredMixin, UpdateView):
    """
    View to update an existing purchase.
    """

    model = Purchase
    form_class = PurchaseForm
    template_name = "transactions/purchases_form.html"

    def get_success_url(self):
        """
        Redirect to the purchases list after successful form submission.
        """
        return reverse("purchaseslist")


class PurchaseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View to delete a purchase.
    """

    model = Purchase
    template_name = "transactions/purchasedelete.html"

    def get_success_url(self):
        """
        Redirect to the purchases list after successful deletion.
        """
        return reverse("purchaseslist")

    def test_func(self):
        """
        Allow deletion only for superusers.
        """
        return self.request.user.is_superuser


class BatchListView(LoginRequiredMixin, ListView):
    model = Batch
    template_name = "transactions/batch_list.html"
    context_object_name = "batches"
    paginate_by = 10
    ordering = ['-manufacturing_date']

class BatchCreateView(LoginRequiredMixin, CreateView):
    model = Batch
    template_name = "transactions/batch_create.html"
    fields = []  # We'll handle fields manually

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Item.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                # Create Batch
                batch = Batch.objects.create(
                    name=request.POST.get('name'),
                    product_id=request.POST.get('product'),
                    manufacturing_date=request.POST.get('manufacturing_date'),
                    expiration_date=request.POST.get('expiration_date'),
                    quantity=int(request.POST.get('quantity')),
                    remarks=request.POST.get('remarks', '')
                )

                # Update product quantity
                product = batch.product
                product.quantity += batch.quantity
                product.save()

                # Process raw materials (direct deduction)
                raw_materials = json.loads(request.POST.get('raw_materials', '[]'))
                for rm in raw_materials:
                    raw_material = RawMaterial.objects.get(id=rm['id'])
                    if raw_material.quantity < rm['quantity_used']:
                        raise ValidationError(
                            f"Not enough {raw_material.name} in stock. "
                            f"Available: {raw_material.quantity}, Needed: {rm['quantity_used']}"
                        )
                    raw_material.quantity -= rm['quantity_used']
                    raw_material.save()

                messages.success(request, 'Batch created successfully')
                return JsonResponse({'status': 'success'})
        
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error creating batch: {str(e)}")
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
        
from django.db.models import F

class BatchDeleteView(LoginRequiredMixin, DeleteView):
    model = Batch
    template_name = "transactions/batch_confirm_delete.html"
    success_url = reverse_lazy('batch-list')

    def delete(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                # Get batch and product FIRST
                batch = self.get_object()
                product = batch.product
                quantity_to_remove = batch.quantity
                
                # Update product quantity using atomic operation
                Item.objects.filter(id=product.id).update(
                    quantity=F('quantity') - quantity_to_remove
                )
                
                # Delete the batch AFTER successful product update
                response = super().delete(request, *args, **kwargs)
                
                messages.success(
                    request,
                    f'Successfully deleted batch and removed {quantity_to_remove} units from {product.name}'
                )
                return response
                
        except Exception as e:
            logger.error(f"Batch deletion error: {str(e)}")
            messages.error(request, f'Error deleting batch: {str(e)}')
            return redirect(self.success_url)
        
class OtherPurchaseListView(LoginRequiredMixin, ListView):
    model = OtherPurchase
    template_name = "transactions/other_purchase_list.html"
    context_object_name = "purchases"
    paginate_by = 10
    ordering = ['-date']

class OtherPurchaseCreateView(LoginRequiredMixin, CreateView):
    model = OtherPurchase
    template_name = "transactions/other_purchase_create.html"
    fields = []  # Explicitly declare empty fields since we're using custom form handling


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get existing vendor names + previous sources
        vendors = Vendor.objects.values_list('name', flat=True).distinct()
        existing_sources = OtherPurchase.objects.exclude(source__isnull=True)\
                                                 .values_list('source', flat=True).distinct()
        context['vendor_sources'] = list(vendors) + list(existing_sources)
        return context

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                data = json.loads(request.body)
                
                # Create OtherPurchase
                purchase = OtherPurchase.objects.create(
                    source=data['source'],
                    date=data['date'],
                    remarks=data.get('remarks', ''),
                    sub_total=Decimal(data['sub_total']),
                    grand_total=Decimal(data['grand_total']),
                    description=f"Other purchase from {data['source']}"
                )

                # Create OtherPurchaseDetailed entries
                for item in data['items']:
                    ops_item = OperationsInventory.objects.get(id=item['id'])
                    OtherPurchaseDetailed.objects.create(
                        other_purchase_id=purchase,
                        type=item['type'],
                        unit_of_measure=ops_item.unit_of_measure,
                        unit_price=Decimal(item['unit_price']),
                        quantity=item['quantity'],
                        total_price=Decimal(item['total'])
                    )
                    # Update inventory
                    ops_item.quantity += item['quantity']
                    ops_item.save()

                return JsonResponse({'status': 'success'})
        
        except Exception as e:
            logger.error(f"Other purchase error: {str(e)}")
            return JsonResponse({'status': 'error', 'error': str(e)}, status=400)

class OtherPurchaseDeleteView(LoginRequiredMixin, DeleteView):
    model = OtherPurchase
    template_name = "transactions/other_purchase_confirm_delete.html"
    success_url = reverse_lazy('other-purchases-list')

    def delete(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                purchase = self.get_object()
                # Restore inventory quantities
                for detail in purchase.details.all():
                    ops_item = OperationsInventory.objects.get(id=detail.raw_material.id)
                    ops_item.quantity -= detail.quantity
                    ops_item.save()
                return super().delete(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f'Error deleting purchase: {str(e)}')
            return redirect(self.success_url)

def get_operations_inventory(request):
    search = request.GET.get('q', '')
    items = OperationsInventory.objects.filter(name__icontains=search)[:10]
    results = [{
        'id': i.id,
        'text': i.name,
        'uom': i.unit_of_measure,
        'type': i.get_type_display(),
        'unit_price': float(i.unit_price),
        'stock': i.quantity
    } for i in items]
    return JsonResponse(results, safe=False)