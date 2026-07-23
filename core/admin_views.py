from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
from .models import Category, SubCategory, BoycottProduct, PakistaniAlternative, UserProfile
from .admin_forms import CategoryForm, SubCategoryForm, ProductForm, AlternativeModerationForm, UserEditForm, UserProfileEditForm

User = get_user_model()

# Trash model mappings (extracted to avoid repetition)
TRASH_MODEL_MAP = {
    'categories': (Category, 'category'),
    'subcategories': (SubCategory, 'subcategory'),
    'products': (BoycottProduct, 'product'),
    'alternatives': (PakistaniAlternative, 'alternative'),
    'users': (User, 'user'),
}

TRASH_MODEL_CLASSES = {
    'categories': Category,
    'subcategories': SubCategory,
    'products': BoycottProduct,
    'alternatives': PakistaniAlternative,
    'users': User,
}


def _admin_required(user):
    return user.is_active and user.is_staff


# ── Dashboard ──────────────────────────────────────────────

@user_passes_test(_admin_required, login_url='/login/')
def admin_overview(request):
    """Admin dashboard overview with stats."""
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)

    stats = {
        'categories': Category.objects.count(),
        'subcategories': SubCategory.objects.count(),
        'products': BoycottProduct.objects.count(),
        'products_verified': BoycottProduct.objects.filter(verified=True).count(),
        'alternatives': PakistaniAlternative.objects.count(),
        'alternatives_pending': PakistaniAlternative.objects.filter(status='pending').count(),
        'alternatives_approved': PakistaniAlternative.objects.filter(status='approved').count(),
        'users': User.objects.count(),
    }

    recent_alternatives = PakistaniAlternative.objects.select_related(
        'product', 'added_by'
    ).order_by('-created_at')[:10]

    return render(request, 'core/admin/overview.html', {
        'stats': stats,
        'recent_alternatives': recent_alternatives,
    })


# ── Category CRUD ──────────────────────────────────────────

@user_passes_test(_admin_required, login_url='/login/')
def admin_category_list(request):
    query = request.GET.get('q', '').strip()
    categories_qs = Category.objects.filter(is_active=True).annotate(
        sub_count=Count('subcategories')
    ).order_by('order', 'name')

    if query:
        categories_qs = categories_qs.filter(
            Q(name__icontains=query) | Q(slug__icontains=query)
        )

    paginator = Paginator(categories_qs, 20)
    categories = paginator.get_page(request.GET.get('page'))

    return render(request, 'core/admin/category_list.html', {
        'categories': categories,
        'search_query': query,
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            if Category.objects.filter(slug=form.cleaned_data['slug']).exists():
                messages.error(request, 'A category with this slug already exists.')
            else:
                form.save()
                messages.success(request, f'✅ Category "{form.cleaned_data["name"]}" created successfully.')
                return redirect('admin_category_list')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = CategoryForm()

    return render(request, 'core/admin/category_form.html', {'mode': 'create', 'form': form})


@user_passes_test(_admin_required, login_url='/login/')
def admin_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            if Category.objects.filter(slug=form.cleaned_data['slug']).exclude(pk=pk).exists():
                messages.error(request, 'A category with this slug already exists.')
            else:
                form.save()
                messages.success(request, f'✅ Category "{form.cleaned_data["name"]}" updated successfully.')
                return redirect('admin_category_list')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = CategoryForm(instance=category)

    return render(request, 'core/admin/category_form.html', {'mode': 'edit', 'form': form, 'category': category})


@user_passes_test(_admin_required, login_url='/login/')
def admin_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.is_active = False
        category.deleted_at = timezone.now()
        category.save()
        messages.success(request, f'🗑️ Category "{name}" moved to trash.')
        return redirect('admin_category_list')
    return render(request, 'core/admin/delete_confirm.html', {
        'object': category,
        'type_name': 'Category',
        'cancel_url': 'admin_category_list',
    })


# ── SubCategory CRUD ───────────────────────────────────────

@user_passes_test(_admin_required, login_url='/login/')
def admin_subcategory_list(request):
    query = request.GET.get('q', '').strip()
    subcategories_qs = SubCategory.objects.filter(is_active=True).select_related('category').annotate(
        product_count=Count('products')
    ).order_by('category__name', 'name')

    if query:
        subcategories_qs = subcategories_qs.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query)
        )

    paginator = Paginator(subcategories_qs, 20)
    subcategories = paginator.get_page(request.GET.get('page'))

    return render(request, 'core/admin/subcategory_list.html', {
        'subcategories': subcategories,
        'search_query': query,
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_subcategory_create(request):
    categories = Category.objects.filter(is_active=True).all()
    if request.method == 'POST':
        form = SubCategoryForm(request.POST)
        if form.is_valid():
            if SubCategory.objects.filter(category=form.cleaned_data['category'], slug=form.cleaned_data['slug']).exists():
                messages.error(request, 'A subcategory with this slug already exists in this category.')
            else:
                form.save()
                messages.success(request, f'✅ Subcategory "{form.cleaned_data["name"]}" created successfully.')
                return redirect('admin_subcategory_list')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = SubCategoryForm()

    return render(request, 'core/admin/subcategory_form.html', {
        'mode': 'create', 'form': form, 'categories': categories
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_subcategory_edit(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    categories = Category.objects.filter(is_active=True).all()
    if request.method == 'POST':
        form = SubCategoryForm(request.POST, instance=subcategory)
        if form.is_valid():
            if SubCategory.objects.filter(category=form.cleaned_data['category'], slug=form.cleaned_data['slug']).exclude(pk=pk).exists():
                messages.error(request, 'A subcategory with this slug already exists in this category.')
            else:
                form.save()
                messages.success(request, f'✅ Subcategory "{form.cleaned_data["name"]}" updated successfully.')
                return redirect('admin_subcategory_list')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = SubCategoryForm(instance=subcategory)

    return render(request, 'core/admin/subcategory_form.html', {
        'mode': 'edit', 'form': form, 'subcategory': subcategory, 'categories': categories
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_subcategory_delete(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    if request.method == 'POST':
        name = subcategory.name
        subcategory.is_active = False
        subcategory.deleted_at = timezone.now()
        subcategory.save()
        messages.success(request, f'🗑️ Subcategory "{name}" moved to trash.')
        return redirect('admin_subcategory_list')
    return render(request, 'core/admin/delete_confirm.html', {
        'object': subcategory,
        'type_name': 'SubCategory',
        'cancel_url': 'admin_subcategory_list',
    })


# ── Product CRUD ───────────────────────────────────────────

@user_passes_test(_admin_required, login_url='/login/')
def admin_product_list(request):
    query = request.GET.get('q', '').strip()
    products_qs = BoycottProduct.objects.filter(is_active=True).select_related(
        'subcategory__category'
    ).annotate(alt_count=Count('alternatives')).order_by('name')

    if query:
        products_qs = products_qs.filter(
            Q(name__icontains=query) | Q(brand__icontains=query) | Q(slug__icontains=query)
        )

    paginator = Paginator(products_qs, 20)
    products = paginator.get_page(request.GET.get('page'))

    return render(request, 'core/admin/product_list.html', {
        'products': products,
        'search_query': query,
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_product_create(request):
    subcategories = SubCategory.objects.filter(is_active=True).select_related('category').all()
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            if BoycottProduct.objects.filter(slug=form.cleaned_data['slug']).exists():
                messages.error(request, 'A product with this slug already exists.')
            else:
                form.save()
                messages.success(request, f'✅ Product "{form.cleaned_data["name"]}" created successfully.')
                return redirect('admin_product_list')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = ProductForm()

    return render(request, 'core/admin/product_form.html', {
        'mode': 'create', 'form': form, 'subcategories': subcategories
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_product_edit(request, pk):
    product = get_object_or_404(BoycottProduct, pk=pk)
    subcategories = SubCategory.objects.filter(is_active=True).select_related('category').all()
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            if BoycottProduct.objects.filter(slug=form.cleaned_data['slug']).exclude(pk=pk).exists():
                messages.error(request, 'A product with this slug already exists.')
            else:
                form.save()
                messages.success(request, f'✅ Product "{form.cleaned_data["name"]}" updated successfully.')
                return redirect('admin_product_list')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = ProductForm(instance=product)

    return render(request, 'core/admin/product_form.html', {
        'mode': 'edit', 'form': form, 'product': product, 'subcategories': subcategories
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_product_delete(request, pk):
    product = get_object_or_404(BoycottProduct, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.is_active = False
        product.deleted_at = timezone.now()
        product.save()
        messages.success(request, f'🗑️ Product "{name}" moved to trash.')
        return redirect('admin_product_list')
    return render(request, 'core/admin/delete_confirm.html', {
        'object': product,
        'type_name': 'Product',
        'cancel_url': 'admin_product_list',
    })


# ── Alternative CRUD ───────────────────────────────────────

@user_passes_test(_admin_required, login_url='/login/')
def admin_alternative_list(request):
    alt_status = request.GET.get('status', '')
    query = request.GET.get('q', '').strip()
    alternatives_qs = PakistaniAlternative.objects.filter(is_active=True).select_related(
        'product', 'added_by', 'reviewed_by'
    ).order_by('-created_at')

    if alt_status:
        alternatives_qs = alternatives_qs.filter(status=alt_status)

    if query:
        alternatives_qs = alternatives_qs.filter(
            Q(name__icontains=query) | Q(brand__icontains=query) | Q(product__name__icontains=query)
        )

    paginator = Paginator(alternatives_qs, 20)
    alternatives = paginator.get_page(request.GET.get('page'))

    return render(request, 'core/admin/alternative_list.html', {
        'alternatives': alternatives,
        'current_status': alt_status,
        'search_query': query,
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_alternative_delete(request, pk):
    alt = get_object_or_404(PakistaniAlternative, pk=pk)
    if request.method == 'POST':
        name = alt.name
        alt.is_active = False
        alt.deleted_at = timezone.now()
        alt.save()
        messages.success(request, f'🗑️ Alternative "{name}" moved to trash.')
        return redirect('admin_alternative_list')
    return render(request, 'core/admin/delete_confirm.html', {
        'object': alt,
        'type_name': 'Alternative',
        'cancel_url': 'admin_alternative_list',
    })


# ── User Management ────────────────────────────────────────

@user_passes_test(_admin_required, login_url='/login/')
def admin_user_list(request):
    query = request.GET.get('q', '').strip()
    users_qs = User.objects.filter(is_active=True).select_related('profile').annotate(
        alt_count=Count('submitted_alternatives')
    ).order_by('-date_joined')

    if query:
        users_qs = users_qs.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(profile__display_name__icontains=query)
        )

    paginator = Paginator(users_qs, 20)
    users = paginator.get_page(request.GET.get('page'))

    return render(request, 'core/admin/user_list.html', {
        'users': users,
        'search_query': query,
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        profile_form = UserProfileEditForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            if User.objects.filter(username=user_form.cleaned_data['username']).exclude(pk=pk).exists():
                messages.error(request, 'A user with this username already exists.')
            else:
                user_form.save()
                profile_form.save()
                messages.success(request, f'✅ User "{user_form.cleaned_data["username"]}" updated successfully.')
                return redirect('admin_user_list')
        else:
            for error in list(user_form.errors.values()) + list(profile_form.errors.values()):
                messages.error(request, error[0])
    else:
        user_form = UserEditForm(instance=user)
        profile_form = UserProfileEditForm(instance=profile)

    return render(request, 'core/admin/user_form.html', {
        'user': user,
        'profile': profile,
        'mode': 'edit',
        'user_form': user_form,
        'profile_form': profile_form,
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_user_toggle_staff(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, 'You cannot change your own staff status.')
        else:
            user.is_staff = not user.is_staff
            user.save()
            action = 'granted' if user.is_staff else 'revoked'
            messages.success(request, f'✅ Staff access {action} for "{user.username}".')
    return redirect('admin_user_list')


@user_passes_test(_admin_required, login_url='/login/')
def admin_user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, 'You cannot delete your own account.')
        else:
            name = user.username
            user.is_active = False
            user.save()
            messages.success(request, f'🗑️ User "{name}" moved to trash.')
        return redirect('admin_user_list')
    return render(request, 'core/admin/delete_confirm.html', {
        'object': user,
        'type_name': 'User',
        'cancel_url': 'admin_user_list',
    })


# ── Trash ────────────────────────────────────────────────────

@user_passes_test(_admin_required, login_url='/login/')
def admin_trash(request):
    """Trash overview showing counts of deleted items."""
    trash_stats = {
        'categories': Category.objects.filter(is_active=False).count(),
        'subcategories': SubCategory.objects.filter(is_active=False).count(),
        'products': BoycottProduct.objects.filter(is_active=False).count(),
        'alternatives': PakistaniAlternative.objects.filter(is_active=False).count(),
        'users': User.objects.filter(is_active=False).count(),
    }
    total_trash = sum(trash_stats.values())

    # Items older than 10 days that can be purged
    purge_cutoff = timezone.now() - timedelta(days=10)
    purgeable = {
        'categories': Category.objects.filter(is_active=False, deleted_at__lt=purge_cutoff).count(),
        'subcategories': SubCategory.objects.filter(is_active=False, deleted_at__lt=purge_cutoff).count(),
        'products': BoycottProduct.objects.filter(is_active=False, deleted_at__lt=purge_cutoff).count(),
        'alternatives': PakistaniAlternative.objects.filter(is_active=False, deleted_at__lt=purge_cutoff).count(),
        'users': User.objects.filter(is_active=False).count(),
    }

    return render(request, 'core/admin/trash.html', {
        'trash_stats': trash_stats,
        'purgeable': purgeable,
        'total_trash': total_trash,
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_trash_list(request, model_type):
    """Generic trash list view for any model type."""
    if model_type not in TRASH_MODEL_MAP:
        messages.error(request, 'Invalid trash type.')
        return redirect('admin_trash')

    model, name = TRASH_MODEL_MAP[model_type]
    query = request.GET.get('q', '').strip()

    if model_type == 'users':
        items_qs = model.objects.filter(is_active=False)
        if query:
            items_qs = items_qs.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(profile__display_name__icontains=query)
            )
    elif model_type == 'alternatives':
        items_qs = model.objects.filter(is_active=False).select_related('product', 'added_by')
        if query:
            items_qs = items_qs.filter(
                Q(name__icontains=query) | Q(brand__icontains=query) | Q(product__name__icontains=query)
            )
    elif model_type == 'products':
        items_qs = model.objects.filter(is_active=False).select_related('subcategory__category')
        if query:
            items_qs = items_qs.filter(
                Q(name__icontains=query) | Q(brand__icontains=query) | Q(slug__icontains=query)
            )
    elif model_type == 'subcategories':
        items_qs = model.objects.filter(is_active=False).select_related('category')
        if query:
            items_qs = items_qs.filter(
                Q(name__icontains=query) | Q(category__name__icontains=query)
            )
    else:
        items_qs = model.objects.filter(is_active=False)
        if query:
            items_qs = items_qs.filter(
                Q(name__icontains=query) | Q(slug__icontains=query)
            )

    if model_type == 'users':
        items_qs = items_qs.order_by('-date_joined')
    else:
        items_qs = items_qs.order_by('-deleted_at')
    paginator = Paginator(items_qs, 20)
    items = paginator.get_page(request.GET.get('page'))

    return render(request, 'core/admin/trash_list.html', {
        'items': items,
        'model_type': model_type,
        'model_name': name,
        'search_query': query,
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_trash_restore(request, model_type, pk):
    """Restore an item from trash."""
    if model_type not in TRASH_MODEL_CLASSES:
        messages.error(request, 'Invalid trash type.')
        return redirect('admin_trash')

    model = TRASH_MODEL_CLASSES[model_type]
    item = get_object_or_404(model, pk=pk, is_active=False)

    if request.method == 'POST':
        item.is_active = True
        if hasattr(item, 'deleted_at'):
            item.deleted_at = None
        item.save()
        messages.success(request, f'✅ {item.name if hasattr(item, "name") else item.username} restored successfully.')
        return redirect('admin_trash_list', model_type=model_type)

    return render(request, 'core/admin/trash_restore_confirm.html', {
        'item': item,
        'model_type': model_type,
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_trash_purge(request, model_type, pk):
    """Permanently delete an item from trash."""
    if model_type not in TRASH_MODEL_CLASSES:
        messages.error(request, 'Invalid trash type.')
        return redirect('admin_trash')

    model = TRASH_MODEL_CLASSES[model_type]
    item = get_object_or_404(model, pk=pk, is_active=False)

    if request.method == 'POST':
        name = item.name if hasattr(item, 'name') else item.username
        item.delete()
        messages.success(request, f'🗑️ {name} permanently deleted.')
        return redirect('admin_trash_list', model_type=model_type)

    return render(request, 'core/admin/trash_purge_confirm.html', {
        'item': item,
        'model_type': model_type,
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_trash_purge_all(request, model_type):
    """Permanently delete all purgeable items (older than 10 days) for a model type."""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_trash')

    if model_type not in TRASH_MODEL_CLASSES:
        messages.error(request, 'Invalid trash type.')
        return redirect('admin_trash')

    model = TRASH_MODEL_CLASSES[model_type]
    purge_cutoff = timezone.now() - timedelta(days=10)
    if model_type == 'users':
        deleted, _ = model.objects.filter(is_active=False).delete()
    else:
        deleted, _ = model.objects.filter(is_active=False, deleted_at__lt=purge_cutoff).delete()

    messages.success(request, f'🗑️ Purged {deleted} items older than 10 days.')
    return redirect('admin_trash')


@user_passes_test(_admin_required, login_url='/login/')
def admin_trash_bulk(request, model_type):
    """Bulk restore or purge selected trashed items."""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_trash_list', model_type=model_type)

    if model_type not in TRASH_MODEL_CLASSES:
        messages.error(request, 'Invalid trash type.')
        return redirect('admin_trash')

    model = TRASH_MODEL_CLASSES[model_type]
    action = request.POST.get('action')
    selected = request.POST.getlist('selected')

    if not selected:
        messages.error(request, 'No items selected.')
        return redirect('admin_trash_list', model_type=model_type)

    pks = [int(pk) for pk in selected if pk.isdigit()]
    items = model.objects.filter(pk__in=pks, is_active=False)

    if action == 'restore':
        restored = 0
        for item in items:
            item.is_active = True
            if hasattr(item, 'deleted_at'):
                item.deleted_at = None
            item.save()
            restored += 1
        messages.success(request, f'✅ Restored {restored} item(s) from trash.')
    elif action == 'purge':
        deleted, _ = items.delete()
        messages.success(request, f'🗑️ Permanently deleted {deleted} item(s).')
    else:
        messages.error(request, 'Invalid bulk action.')

    return redirect('admin_trash_list', model_type=model_type)

