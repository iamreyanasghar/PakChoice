from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from .models import Category, SubCategory, BoycottProduct, PakistaniAlternative, UserProfile


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
    categories = Category.objects.annotate(
        sub_count=Count('subcategories')
    ).order_by('order', 'name')
    return render(request, 'core/admin/category_list.html', {'categories': categories})


@user_passes_test(_admin_required, login_url='/login/')
def admin_category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        icon = request.POST.get('icon', '📦').strip()
        description = request.POST.get('description', '').strip()
        order = request.POST.get('order', 0)

        if not name or not slug:
            messages.error(request, 'Name and slug are required.')
        elif Category.objects.filter(slug=slug).exists():
            messages.error(request, 'A category with this slug already exists.')
        else:
            Category.objects.create(name=name, slug=slug, icon=icon, description=description, order=order)
            messages.success(request, f'✅ Category "{name}" created successfully.')
            return redirect('admin_category_list')

    return render(request, 'core/admin/category_form.html', {'mode': 'create'})


@user_passes_test(_admin_required, login_url='/login/')
def admin_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        icon = request.POST.get('icon', '📦').strip()
        description = request.POST.get('description', '').strip()
        order = request.POST.get('order', 0)

        if not name or not slug:
            messages.error(request, 'Name and slug are required.')
        elif Category.objects.filter(slug=slug).exclude(pk=pk).exists():
            messages.error(request, 'A category with this slug already exists.')
        else:
            category.name = name
            category.slug = slug
            category.icon = icon
            category.description = description
            category.order = order
            category.save()
            messages.success(request, f'✅ Category "{name}" updated successfully.')
            return redirect('admin_category_list')

    return render(request, 'core/admin/category_form.html', {'mode': 'edit', 'category': category})


@user_passes_test(_admin_required, login_url='/login/')
def admin_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'🗑️ Category "{name}" deleted successfully.')
        return redirect('admin_category_list')
    return render(request, 'core/admin/delete_confirm.html', {
        'object': category,
        'type_name': 'Category',
        'cancel_url': 'admin_category_list',
    })


# ── SubCategory CRUD ───────────────────────────────────────

@user_passes_test(_admin_required, login_url='/login/')
def admin_subcategory_list(request):
    subcategories = SubCategory.objects.select_related('category').annotate(
        product_count=Count('products')
    ).order_by('category__name', 'name')
    return render(request, 'core/admin/subcategory_list.html', {'subcategories': subcategories})


@user_passes_test(_admin_required, login_url='/login/')
def admin_subcategory_create(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        category_id = request.POST.get('category')
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        icon = request.POST.get('icon', '📦').strip()

        category = get_object_or_404(Category, pk=category_id) if category_id else None

        if not name or not slug or not category:
            messages.error(request, 'All required fields must be filled.')
        elif SubCategory.objects.filter(category=category, slug=slug).exists():
            messages.error(request, 'A subcategory with this slug already exists in this category.')
        else:
            SubCategory.objects.create(category=category, name=name, slug=slug, icon=icon)
            messages.success(request, f'✅ Subcategory "{name}" created successfully.')
            return redirect('admin_subcategory_list')

    return render(request, 'core/admin/subcategory_form.html', {
        'mode': 'create', 'categories': categories
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_subcategory_edit(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    categories = Category.objects.all()
    if request.method == 'POST':
        category_id = request.POST.get('category')
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        icon = request.POST.get('icon', '📦').strip()

        category = get_object_or_404(Category, pk=category_id) if category_id else None

        if not name or not slug or not category:
            messages.error(request, 'All required fields must be filled.')
        elif SubCategory.objects.filter(category=category, slug=slug).exclude(pk=pk).exists():
            messages.error(request, 'A subcategory with this slug already exists in this category.')
        else:
            subcategory.category = category
            subcategory.name = name
            subcategory.slug = slug
            subcategory.icon = icon
            subcategory.save()
            messages.success(request, f'✅ Subcategory "{name}" updated successfully.')
            return redirect('admin_subcategory_list')

    return render(request, 'core/admin/subcategory_form.html', {
        'mode': 'edit', 'subcategory': subcategory, 'categories': categories
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_subcategory_delete(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    if request.method == 'POST':
        name = subcategory.name
        subcategory.delete()
        messages.success(request, f'🗑️ Subcategory "{name}" deleted successfully.')
        return redirect('admin_subcategory_list')
    return render(request, 'core/admin/delete_confirm.html', {
        'object': subcategory,
        'type_name': 'SubCategory',
        'cancel_url': 'admin_subcategory_list',
    })


# ── Product CRUD ───────────────────────────────────────────

@user_passes_test(_admin_required, login_url='/login/')
def admin_product_list(request):
    products = BoycottProduct.objects.select_related(
        'subcategory__category'
    ).annotate(alt_count=Count('alternatives')).order_by('name')
    return render(request, 'core/admin/product_list.html', {'products': products})


@user_passes_test(_admin_required, login_url='/login/')
def admin_product_create(request):
    subcategories = SubCategory.objects.select_related('category').all()
    if request.method == 'POST':
        subcategory_id = request.POST.get('subcategory')
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        brand = request.POST.get('brand', '').strip()
        country = request.POST.get('country_of_origin', '').strip()
        reason = request.POST.get('reason', '').strip()
        image_url = request.POST.get('image_url', '').strip()
        logo_url = request.POST.get('logo_url', '').strip()
        verified = request.POST.get('verified') == 'on'

        subcategory = get_object_or_404(SubCategory, pk=subcategory_id) if subcategory_id else None

        if not name or not slug or not brand or not subcategory:
            messages.error(request, 'Required fields: Name, Slug, Brand, and Subcategory.')
        elif BoycottProduct.objects.filter(slug=slug).exists():
            messages.error(request, 'A product with this slug already exists.')
        else:
            BoycottProduct.objects.create(
                subcategory=subcategory, name=name, slug=slug, brand=brand,
                country_of_origin=country, reason=reason,
                image_url=image_url, logo_url=logo_url, verified=verified,
            )
            messages.success(request, f'✅ Product "{name}" created successfully.')
            return redirect('admin_product_list')

    return render(request, 'core/admin/product_form.html', {
        'mode': 'create', 'subcategories': subcategories
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_product_edit(request, pk):
    product = get_object_or_404(BoycottProduct, pk=pk)
    subcategories = SubCategory.objects.select_related('category').all()
    if request.method == 'POST':
        subcategory_id = request.POST.get('subcategory')
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        brand = request.POST.get('brand', '').strip()
        country = request.POST.get('country_of_origin', '').strip()
        reason = request.POST.get('reason', '').strip()
        image_url = request.POST.get('image_url', '').strip()
        logo_url = request.POST.get('logo_url', '').strip()
        verified = request.POST.get('verified') == 'on'

        subcategory = get_object_or_404(SubCategory, pk=subcategory_id) if subcategory_id else None

        if not name or not slug or not brand or not subcategory:
            messages.error(request, 'Required fields: Name, Slug, Brand, and Subcategory.')
        elif BoycottProduct.objects.filter(slug=slug).exclude(pk=pk).exists():
            messages.error(request, 'A product with this slug already exists.')
        else:
            product.subcategory = subcategory
            product.name = name
            product.slug = slug
            product.brand = brand
            product.country_of_origin = country
            product.reason = reason
            product.image_url = image_url
            product.logo_url = logo_url
            product.verified = verified
            product.save()
            messages.success(request, f'✅ Product "{name}" updated successfully.')
            return redirect('admin_product_list')

    return render(request, 'core/admin/product_form.html', {
        'mode': 'edit', 'product': product, 'subcategories': subcategories
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_product_delete(request, pk):
    product = get_object_or_404(BoycottProduct, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'🗑️ Product "{name}" deleted successfully.')
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
    alternatives = PakistaniAlternative.objects.select_related(
        'product', 'added_by', 'reviewed_by'
    ).order_by('-created_at')

    if alt_status:
        alternatives = alternatives.filter(status=alt_status)

    return render(request, 'core/admin/alternative_list.html', {
        'alternatives': alternatives,
        'current_status': alt_status,
    })


@user_passes_test(_admin_required, login_url='/login/')
def admin_alternative_delete(request, pk):
    alt = get_object_or_404(PakistaniAlternative, pk=pk)
    if request.method == 'POST':
        name = alt.name
        alt.delete()
        messages.success(request, f'🗑️ Alternative "{name}" deleted successfully.')
        return redirect('admin_alternative_list')
    return render(request, 'core/admin/delete_confirm.html', {
        'object': alt,
        'type_name': 'Alternative',
        'cancel_url': 'admin_alternative_list',
    })


# ── User Management ────────────────────────────────────────

@user_passes_test(_admin_required, login_url='/login/')
def admin_user_list(request):
    users = User.objects.select_related('profile').annotate(
        alt_count=Count('submitted_alternatives')
    ).order_by('-date_joined')
    return render(request, 'core/admin/user_list.html', {'users': users})


@user_passes_test(_admin_required, login_url='/login/')
def admin_user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        display_name = request.POST.get('display_name', '').strip()
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        is_active = request.POST.get('is_active') == 'on'

        if not username or not email:
            messages.error(request, 'Username and email are required.')
        elif User.objects.filter(username=username).exclude(pk=pk).exists():
            messages.error(request, 'A user with this username already exists.')
        elif User.objects.filter(email=email).exclude(pk=pk).exists():
            messages.error(request, 'A user with this email already exists.')
        else:
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.is_active = is_active
            user.save()
            profile.display_name = display_name
            profile.save()
            messages.success(request, f'✅ User "{username}" updated successfully.')
            return redirect('admin_user_list')

    return render(request, 'core/admin/user_form.html', {
        'user': user,
        'profile': profile,
        'mode': 'edit',
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
            user.delete()
            messages.success(request, f'🗑️ User "{name}" deleted successfully.')
        return redirect('admin_user_list')
    return render(request, 'core/admin/delete_confirm.html', {
        'object': user,
        'type_name': 'User',
        'cancel_url': 'admin_user_list',
    })

