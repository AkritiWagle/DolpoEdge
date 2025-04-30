"""
Module: store.views

Contains Django views for managing items, profiles,
and deliveries in the store application.

Classes handle product listing, creation, updating,
deletion, and delivery management.
The module integrates with Django's authentication
and querying functionalities.
"""

# Standard library imports
import operator
import qrcode
from io import BytesIO
from functools import reduce

# Django core imports
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum

# Authentication and permissions
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test


# Class-based views
from django.views.generic import (
    DetailView, CreateView, UpdateView, DeleteView, ListView
)
from django.views.generic.edit import FormMixin

# Third-party packages
from django_tables2 import SingleTableView
import django_tables2 as tables
from django_tables2.export.views import ExportMixin

# Local app imports
from accounts.models import Profile, Vendor
from transactions.models import Sale
from .models import Category, Item, Delivery, RawMaterial, OperationsInventory, BaseRecipe, RecipeIngredient
from .forms import ItemForm, CategoryForm, DeliveryForm, RawMaterialForm, OperationsInventoryForm, BaseRecipeForm, RecipeIngredientForm, RecipeIngredientFormSet, RecipeGeneratorForm
from .tables import ItemTable


@login_required
def dashboard(request):
    profiles = Profile.objects.all()
    Category.objects.annotate(nitem=Count("item"))
    items = Item.objects.all()
    total_items = (
        Item.objects.all()
        .aggregate(Sum("quantity"))
        .get("quantity__sum", 0.00)
    )
    items_count = items.count()
    profiles_count = profiles.count()

    # Prepare data for charts
    category_counts = Category.objects.annotate(
        item_count=Count("item")
    ).values("name", "item_count")
    categories = [cat["name"] for cat in category_counts]
    category_counts = [cat["item_count"] for cat in category_counts]

    sale_dates = (
        Sale.objects.values("date_added__date")
        .annotate(total_sales=Sum("grand_total"))
        .order_by("date_added__date")
    )
    sale_dates_labels = [
        date["date_added__date"].strftime("%Y-%m-%d") for date in sale_dates
    ]
    sale_dates_values = [float(date["total_sales"]) for date in sale_dates]

    context = {
        "items": items,
        "profiles": profiles,
        "profiles_count": profiles_count,
        "items_count": items_count,
        "total_items": total_items,
        "vendors": Vendor.objects.all(),
        "delivery": Delivery.objects.all(),
        "sales": Sale.objects.all(),
        "categories": categories,
        "category_counts": category_counts,
        "sale_dates_labels": sale_dates_labels,
        "sale_dates_values": sale_dates_values,
    }
    return render(request, "store/dashboard.html", context)

#for notification
def notifications(request):
    return render(request, 'store/notifications.html', {'message': 'No notifications'})



class ProductListView(LoginRequiredMixin, ExportMixin, tables.SingleTableView):
    """
    View class to display a list of products.

    Attributes:
    - model: The model associated with the view.
    - table_class: The table class used for rendering.
    - template_name: The HTML template used for rendering the view.
    - context_object_name: The variable name for the context object.
    - paginate_by: Number of items per page for pagination.
    """

    model = Item
    table_class = ItemTable
    template_name = "store/productslist.html"
    context_object_name = "items"
    paginate_by = 10
    SingleTableView.table_pagination = False


class ItemSearchListView(ProductListView):
    """
    View class to search and display a filtered list of items.

    Attributes:
    - paginate_by: Number of items per page for pagination.
    """

    paginate_by = 10

    def get_queryset(self):
        result = super(ItemSearchListView, self).get_queryset()

        query = self.request.GET.get("q")
        if query:
            query_list = query.split()
            result = result.filter(
                reduce(
                    operator.and_, (Q(name__icontains=q) for q in query_list)
                )
            )
        return result


class ProductDetailView(LoginRequiredMixin, FormMixin, DetailView):
    """
    View class to display detailed information about a product.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    """

    model = Item
    template_name = "store/productdetail.html"

    def get_success_url(self):
        return reverse("product-detail", kwargs={"slug": self.object.slug})


class ProductCreateView(LoginRequiredMixin, CreateView):
    """
    View class to create a new product.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    - form_class: The form class used for data input.
    - success_url: The URL to redirect to upon successful form submission.
    """

    model = Item
    template_name = "store/productcreate.html"
    form_class = ItemForm
    success_url = "/products"

    def test_func(self):
        # item = Item.objects.get(id=pk)
        if self.request.POST.get("quantity") < 1:
            return False
        else:
            return True


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View class to update product information.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    - fields: The fields to be updated.
    - success_url: The URL to redirect to upon successful form submission.
    """

    model = Item
    template_name = "store/productupdate.html"
    form_class = ItemForm
    success_url = "/products"

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View class to delete a product.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    - success_url: The URL to redirect to upon successful deletion.
    """

    model = Item
    template_name = "store/productdelete.html"
    success_url = "/products"

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False


class DeliveryListView(
    LoginRequiredMixin, ExportMixin, tables.SingleTableView
):
    """
    View class to display a list of deliveries.

    Attributes:
    - model: The model associated with the view.
    - pagination: Number of items per page for pagination.
    - template_name: The HTML template used for rendering the view.
    - context_object_name: The variable name for the context object.
    """

    model = Delivery
    pagination = 10
    template_name = "store/deliveries.html"
    context_object_name = "deliveries"


class DeliverySearchListView(DeliveryListView):
    """
    View class to search and display a filtered list of deliveries.

    Attributes:
    - paginate_by: Number of items per page for pagination.
    """

    paginate_by = 10

    def get_queryset(self):
        result = super(DeliverySearchListView, self).get_queryset()

        query = self.request.GET.get("q")
        if query:
            query_list = query.split()
            result = result.filter(
                reduce(
                    operator.
                    and_, (Q(customer_name__icontains=q) for q in query_list)
                )
            )
        return result


class DeliveryDetailView(LoginRequiredMixin, DetailView):
    """
    View class to display detailed information about a delivery.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    """

    model = Delivery
    template_name = "store/deliverydetail.html"


class DeliveryCreateView(LoginRequiredMixin, CreateView):
    """
    View class to create a new delivery.

    Attributes:
    - model: The model associated with the view.
    - fields: The fields to be included in the form.
    - template_name: The HTML template used for rendering the view.
    - success_url: The URL to redirect to upon successful form submission.
    """

    model = Delivery
    form_class = DeliveryForm
    template_name = "store/delivery_form.html"
    success_url = "/deliveries"


class DeliveryUpdateView(LoginRequiredMixin, UpdateView):
    """
    View class to update delivery information.

    Attributes:
    - model: The model associated with the view.
    - fields: The fields to be updated.
    - template_name: The HTML template used for rendering the view.
    - success_url: The URL to redirect to upon successful form submission.
    """

    model = Delivery
    form_class = DeliveryForm
    template_name = "store/delivery_form.html"
    success_url = "/deliveries"


class DeliveryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View class to delete a delivery.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    - success_url: The URL to redirect to upon successful deletion.
    """

    model = Delivery
    template_name = "store/productdelete.html"
    success_url = "/deliveries"

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'store/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10
    login_url = 'login'


class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'store/category_detail.html'
    context_object_name = 'category'
    login_url = 'login'


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    template_name = 'store/category_form.html'
    form_class = CategoryForm
    login_url = 'login'

    def get_success_url(self):
        return reverse_lazy('category-detail', kwargs={'pk': self.object.pk})


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    template_name = 'store/category_form.html'
    form_class = CategoryForm
    login_url = 'login'

    def get_success_url(self):
        return reverse_lazy('category-detail', kwargs={'pk': self.object.pk})


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'store/category_confirm_delete.html'
    context_object_name = 'category'
    success_url = reverse_lazy('category-list')
    login_url = 'login'

class RawMaterialListView(ListView):
    model = RawMaterial
    template_name = 'store/raw_material_list.html'
    context_object_name = 'raw_materials'
    paginate_by = 10
    ordering = ['-created_at']  # Add explicit ordering

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        
        if query:
            return queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(remarks__icontains=query) |
                Q(vendor__name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context

class RawMaterialCreateView(CreateView):
    model = RawMaterial
    form_class = RawMaterialForm
    template_name = 'store/raw_material_form.html'
    success_url = reverse_lazy('raw-material-list')

class RawMaterialUpdateView(UpdateView):
    model = RawMaterial
    form_class = RawMaterialForm
    template_name = 'store/raw_material_form.html'
    success_url = reverse_lazy('raw-material-list')

class RawMaterialDeleteView(DeleteView):
    model = RawMaterial
    template_name = 'store/raw_material_confirm_delete.html'  # Add this line
    success_url = reverse_lazy('raw-material-list')
    
    # Optional: Add context data if needed
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.get_object()
        return context

class RawMaterialDetailView(DetailView):
    model = RawMaterial
    template_name = 'store/raw_material_detail.html'
    context_object_name = 'material'

class RawMaterialSearchView(ListView):
    model = RawMaterial
    template_name = 'store/raw_material_list.html'
    context_object_name = 'raw_materials'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        
        if query:
            return queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(remarks__icontains=query) |
                Q(vendor__name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class OperationsInventoryListView(LoginRequiredMixin, ListView):
    model = OperationsInventory
    template_name = 'store/operations_inventory_list.html'
    context_object_name = 'operations_inventory'
    paginate_by = 10

    def get_queryset(self):
        search_query = self.request.GET.get('q', '')
        queryset = super().get_queryset()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        return queryset.order_by('-created_at')

class OperationsInventoryCreateView(LoginRequiredMixin, CreateView):
    model = OperationsInventory
    form_class = OperationsInventoryForm
    template_name = 'store/operations_inventory_form.html'
    success_url = reverse_lazy('operations-inventory-list')

class OperationsInventoryUpdateView(LoginRequiredMixin, UpdateView):
    model = OperationsInventory
    form_class = OperationsInventoryForm
    template_name = 'store/operations_inventory_form.html'
    success_url = reverse_lazy('operations-inventory-list')

class OperationsInventoryDeleteView(LoginRequiredMixin, DeleteView):
    model = OperationsInventory
    template_name = 'store/operations_inventory_confirm_delete.html'
    success_url = reverse_lazy('operations-inventory-list')


def product_qr_code(request, slug):
    # Retrieve the product details
    product = get_object_or_404(Item, slug=slug)
    # You can customize the data as needed
    data = (
        f"B.M Industries\n\n"
        f"Dolpo Edge\n\n"
        f"Product: {product.name}\n"
        f"Category: {product.category.name}\n"
        f"Selling Price: {product.selling_price}\n"
        f"Quantity: {product.quantity}"
    )
    
    # Generate the QR code
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type="image/png")


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@csrf_exempt
@require_POST
@login_required
def get_items_ajax_view(request):
    if is_ajax(request):
        try:
            term = request.POST.get("term", "")
            data = []

            items = Item.objects.filter(name__icontains=term)
            for item in items[:10]:
                data.append(item.to_json())

            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Not an AJAX request'}, status=400)


def admin_required(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@user_passes_test(admin_required)
@user_passes_test(admin_required)
def recipe_create(request):
    if request.method == 'POST':
        form = BaseRecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.created_by = request.user
            recipe.save()
            return redirect('add_ingredients', recipe_id=recipe.id)
    else:
        form = BaseRecipeForm()
    return render(request, 'store/recipe_create.html', {'form': form})

@user_passes_test(admin_required)
def add_ingredients(request, recipe_id):
    recipe = get_object_or_404(BaseRecipe, pk=recipe_id)
    ingredients = recipe.ingredients.all()
    
    if request.method == 'POST':
        form = RecipeIngredientForm(request.POST)
        if form.is_valid():
            ingredient = form.save(commit=False)
            ingredient.recipe = recipe
            ingredient.unit_of_measure = ingredient.raw_material.unit_of_measure
            ingredient.save()
            return redirect('add_ingredients', recipe_id=recipe.id)
    else:
        form = RecipeIngredientForm()

    return render(request, 'store/add_ingredients.html', {
        'recipe': recipe,
        'form': form,
        'ingredients': ingredients
    })

@user_passes_test(admin_required)
def delete_ingredient(request, pk):
    ingredient = get_object_or_404(RecipeIngredient, pk=pk)
    recipe_id = ingredient.recipe.id
    ingredient.delete()
    return redirect('add_ingredients', recipe_id=recipe_id)

@user_passes_test(admin_required)
def recipe_list(request):
    recipes = BaseRecipe.objects.all()
    return render(request, 'store/recipe_list.html', {'recipes': recipes})

@user_passes_test(admin_required)
def recipe_delete(request, pk):
    recipe = get_object_or_404(BaseRecipe, pk=pk)
    if request.method == 'POST':
        recipe.delete()
        return redirect('recipe_list')
    return render(request, 'store/recipe_confirm_delete.html', {'recipe': recipe})

@user_passes_test(admin_required)
def recipe_generator(request):
    calculated = False
    results = []
    if request.method == 'POST':
        form = RecipeGeneratorForm(request.POST)
        if form.is_valid():
            base_recipe = form.cleaned_data['base_recipe']
            desired_quantity = form.cleaned_data['desired_quantity']
            
            # Calculate ratio
            ratio = desired_quantity / base_recipe.final_product_quantity
            
            # Calculate scaled ingredients
            for ingredient in base_recipe.ingredients.all():
                scaled_quantity = ingredient.quantity * ratio
                results.append({
                    'raw_material': ingredient.raw_material,
                    'quantity': scaled_quantity,
                    'unit': ingredient.unit_of_measure,
                })
            calculated = True
    else:
        form = RecipeGeneratorForm()

    return render(request, 'store/recipe_generator.html', {
        'form': form,
        'results': results,
        'calculated': calculated
    })