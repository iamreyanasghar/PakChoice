import os
import uuid
from urllib.parse import urlparse

import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth import login, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Q, F, Count
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .decorators import rate_limit
from .security_logger import log_security_event
from .models import Category, SubCategory, Product, Alternative, Vote, UserProfile, ProductSuggestion, Report
from .forms import RegisterForm, LoginForm, AlternativeForm, AvatarForm, ProfileSettingsForm, PasswordChangeForm, ModerationForm, ForgotPasswordForm, VerifySecurityForm, ResetPasswordForm, SecuritySettingsForm, ProductSuggestionForm

User = get_user_model()

def _staff_required(user):
    return user.is_active and user.is_staff


def download_image_from_url(image_url, folder):
    """
    Download an image from a URL and save it to static/img/<folder>/.
    Returns the relative path (e.g. 'boycott/abc123.jpg') or None on failure.
    """
    try:
        parsed = urlparse(image_url)
        ext = os.path.splitext(parsed.path)[1] or '.jpg'
        filename = f'{uuid.uuid4().hex}{ext}'
        from django.conf import settings
        save_path = os.path.join(settings.BASE_DIR, 'static', 'img', folder, filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        headers = {'User-Agent': 'Mozilla/5.0'}
        with requests.get(image_url, headers=headers, timeout=15, stream=True) as response:
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                return None
            content_length = response.headers.get('Content-Length')
            max_size = 2 * 1024 * 1024  # 2 MB
            if content_length and int(content_length) > max_size:
                return None
            total = 0
            with open(save_path, 'wb') as destination:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        total += len(chunk)
                        if total > max_size:
                            destination.close()
                            os.remove(save_path)
                            return None
                        destination.write(chunk)
        return f'{folder}/{filename}'
    except Exception:
        return None


def health(request):
    return JsonResponse({"status": "ok"})


def custom_404(request, exception):
    return render(request, 'core/404.html', status=404)


def custom_500(request):
    return render(request, 'core/500.html', status=500)


def sitemap(request):
    """Generate a simple XML sitemap of public pages."""
    from django.urls import reverse
    from django.utils import timezone
    
    urls = [
        {'loc': request.build_absolute_uri(reverse('home')), 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': request.build_absolute_uri(reverse('search')), 'priority': '0.8', 'changefreq': 'daily'},
    ]
    
    # Add categories
    for category in Category.objects.filter(is_active=True):
        urls.append({
            'loc': request.build_absolute_uri(reverse('category_detail', args=[category.slug])),
            'priority': '0.7',
            'changefreq': 'weekly',
            'lastmod': category.updated_at.isoformat() if category.updated_at else timezone.now().isoformat(),
        })
    
    # Add subcategories
    for subcategory in SubCategory.objects.filter(is_active=True).select_related('category'):
        urls.append({
            'loc': request.build_absolute_uri(reverse('subcategory_detail', args=[subcategory.category.slug, subcategory.slug])),
            'priority': '0.6',
            'changefreq': 'weekly',
            'lastmod': subcategory.updated_at.isoformat() if subcategory.updated_at else timezone.now().isoformat(),
        })
    
    # Add products
    for product in Product.objects.filter(verified=True, is_active=True):
        urls.append({
            'loc': request.build_absolute_uri(reverse('product_detail', args=[product.slug])),
            'priority': '0.5',
            'changefreq': 'weekly',
            'lastmod': product.updated_at.isoformat() if product.updated_at else timezone.now().isoformat(),
        })
    
    from django.utils.html import escape
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url in urls:
        xml.append('  <url>')
        xml.append(f'    <loc>{escape(url["loc"])}</loc>')
        if 'lastmod' in url:
            xml.append(f'    <lastmod>{escape(url["lastmod"])}</lastmod>')
        xml.append(f'    <changefreq>{escape(url["changefreq"])}</changefreq>')
        xml.append(f'    <priority>{escape(url["priority"])}</priority>')
        xml.append('  </url>')
    xml.append('</urlset>')

    return HttpResponse('\n'.join(xml), content_type='application/xml')


def home(request):
    categories = Category.objects.filter(is_active=True).annotate(
        subcategory_count=Count('subcategories')
    ).prefetch_related('subcategories').all()
    total_products = Product.objects.filter(verified=True, is_active=True).count()
    total_alternatives = Alternative.objects.filter(status='approved', is_active=True).count()
    return render(request, 'core/home.html', {
        'categories': categories,
        'total_products': total_products,
        'total_alternatives': total_alternatives,
    })


def category_detail(request, slug):
    try:
        category = get_object_or_404(Category, slug=slug, is_active=True)
    except Http404:
        return render(request, 'core/404.html', status=404)
    subcategories = category.subcategories.filter(is_active=True).annotate(
        product_count=Count('products')
    ).prefetch_related('products').all()
    return render(request, 'core/category.html', {'category': category, 'subcategories': subcategories})


def subcategory_detail(request, cat_slug, sub_slug):
    try:
        category = get_object_or_404(Category, slug=cat_slug, is_active=True)
        subcategory = get_object_or_404(SubCategory, category=category, slug=sub_slug, is_active=True)
    except Http404:
        return render(request, 'core/404.html', status=404)
    products = subcategory.products.filter(verified=True, is_active=True).annotate(
        alternative_count=Count('alternatives')
    ).prefetch_related('alternatives')
    return render(request, 'core/subcategory.html', {
        'category': category, 'subcategory': subcategory, 'products': products
    })


def product_detail(request, slug):
    try:
        product = get_object_or_404(Product, slug=slug, is_active=True)
    except Http404:
        return render(request, 'core/404.html', status=404)
    alternatives = product.alternatives.filter(status='approved', is_active=True)
    user_votes = set()
    if request.user.is_authenticated:
        user_votes = set(Vote.objects.filter(
            user=request.user, alternative__in=alternatives
        ).values_list('alternative_id', flat=True))
    form = AlternativeForm()
    return render(request, 'core/product.html', {
        'product': product, 'alternatives': alternatives,
        'form': form, 'user_votes': user_votes,
    })


def suggest_product(request):
    form = ProductSuggestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        suggestion = form.save(commit=False)
        if request.user.is_authenticated:
            suggestion.submitted_by = request.user
        suggestion.save()
        messages.success(request, '✅ Suggestion submitted! Our team will review it shortly.')
        return redirect('suggest_product')
    return render(request, 'core/suggest_product.html', {'form': form})


@require_POST
def add_alternative(request, slug):
    try:
        product = get_object_or_404(Product, slug=slug)
    except Http404:
        return render(request, 'core/404.html', status=404)
    form = AlternativeForm(request.POST, request.FILES)
    if form.is_valid():
        alt = form.save(commit=False)
        alt.product = product
        alt.added_by = request.user if request.user.is_authenticated else None
        alt.status = 'pending'
        if alt.image_url:
            alt.local_image = download_image_from_url(alt.image_url, 'alternative')
        alt.save()
        messages.success(request, '✅ Alternative submitted! It will appear after admin review.')
    else:
        for error in form.errors.values():
            messages.error(request, error[0])
    return redirect('product_detail', slug=slug)


@require_POST
@rate_limit(key_prefix='upvote', limit=30, period=60)
def upvote_alternative(request, pk):
    try:
        alt = get_object_or_404(Alternative, pk=pk, status='approved')
    except Http404:
        return render(request, 'core/404.html', status=404)
    with transaction.atomic():
        alt = Alternative.objects.select_for_update().get(pk=pk)
        voted = False
        if request.user.is_authenticated:
            existing_vote = Vote.objects.filter(
                user=request.user, alternative=alt
            ).first()
            if existing_vote:
                existing_vote.delete()
                alt.upvotes = F('upvotes') - 1
                voted = False
            else:
                Vote.objects.create(user=request.user, alternative=alt)
                alt.upvotes = F('upvotes') + 1
                voted = True
        else:
            # Anonymous users: track votes in session
            voted_alternatives = request.session.get('voted_alternatives', [])
            if pk in voted_alternatives:
                # Remove vote
                voted_alternatives.remove(pk)
                alt.upvotes = F('upvotes') - 1
                voted = False
            else:
                # Add vote
                voted_alternatives.append(pk)
                alt.upvotes = F('upvotes') + 1
                voted = True
            request.session['voted_alternatives'] = voted_alternatives
            request.session.modified = True
        alt.save()
        alt.refresh_from_db(fields=['upvotes'])
    return JsonResponse({'upvotes': max(0, alt.upvotes), 'voted': voted})


from django.core.paginator import Paginator


def search_suggestions(request):
    """Return autocomplete suggestions for the search bar."""
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 1:
        return JsonResponse({'suggestions': []})

    suggestions = set()

    # Match category names
    for name in Category.objects.filter(is_active=True, name__icontains=q).values_list('name', flat=True):
        suggestions.add(name)

    # Match subcategory names
    for name in SubCategory.objects.filter(is_active=True, name__icontains=q).values_list('name', flat=True):
        suggestions.add(name)

    # Match product names and brands
    for name in Product.objects.filter(is_active=True, verified=True).filter(
        Q(name__icontains=q) | Q(brand__icontains=q)
    ).values_list('name', flat=True):
        suggestions.add(name)

    # Match alternative names
    for name in Alternative.objects.filter(is_active=True, status='approved').filter(
        Q(name__icontains=q) | Q(brand__icontains=q)
    ).values_list('name', flat=True):
        suggestions.add(name)

    return JsonResponse({'suggestions': sorted(suggestions)[:8]})


def search(request):
    q = request.GET.get('q', '').strip()
    products, categories, subcategories, alternatives = [], [], [], []
    product_page = request.GET.get('product_page', 1)
    category_page = request.GET.get('category_page', 1)
    subcategory_page = request.GET.get('subcategory_page', 1)
    alternative_page = request.GET.get('alternative_page', 1)

    if q:
        products_qs = Product.objects.filter(
            Q(name__icontains=q) | Q(brand__icontains=q) | Q(reason__icontains=q),
            is_active=True
        ).select_related('subcategory__category')
        products_paginator = Paginator(products_qs, 10)
        products = products_paginator.get_page(product_page)

        categories_qs = Category.objects.filter(
            Q(name__icontains=q) | Q(description__icontains=q),
            is_active=True
        )
        categories_paginator = Paginator(categories_qs, 10)
        categories = categories_paginator.get_page(category_page)

        subcategories_qs = SubCategory.objects.filter(
            Q(name__icontains=q) | Q(category__name__icontains=q),
            is_active=True
        ).select_related('category')
        subcategories_paginator = Paginator(subcategories_qs, 10)
        subcategories = subcategories_paginator.get_page(subcategory_page)

        alternatives_qs = Alternative.objects.filter(
            Q(name__icontains=q) | Q(brand__icontains=q) | Q(description__icontains=q),
            status='approved',
            is_active=True
        ).select_related('product__subcategory__category')
        alternatives_paginator = Paginator(alternatives_qs, 10)
        alternatives = alternatives_paginator.get_page(alternative_page)

    # Dynamic suggestions from popular categories and products
    suggestions = list(Category.objects.filter(is_active=True).order_by('order')[:6].values_list('name', flat=True))
    popular_products = list(Product.objects.filter(verified=True, is_active=True).order_by('name')[:4].values_list('name', flat=True))
    suggestions.extend(popular_products)

    total = 0
    if products:
        total += products.paginator.count
    if categories:
        total += categories.paginator.count
    if subcategories:
        total += subcategories.paginator.count
    if alternatives:
        total += alternatives.paginator.count

    return render(request, 'core/search.html', {
        'products': products,
        'categories': categories,
        'subcategories': subcategories,
        'alternatives': alternatives,
        'query': q,
        'total': total,
        'suggestions': suggestions[:10],
    })


def register_view(request):
    return render(request, 'core/temporarily_unavailable.html', {
        'title': 'Registration Temporarily Unavailable',
        'message': 'User registration is currently disabled. Please check back later.',
    }, status=503)


def login_view(request):
    return render(request, 'core/temporarily_unavailable.html', {
        'title': 'Login Temporarily Unavailable',
        'message': 'User login is currently disabled. Please use the admin login at /admin if you are a staff member.',
    }, status=503)


@require_POST
def logout_view(request):
    logout(request)
    return redirect('home')


@rate_limit(key_prefix='admin_login', limit=5, period=300)
def admin_login_view(request):
    """Admin-only login page at /admin."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_overview')

    from django.contrib.auth.forms import AuthenticationForm
    form = AuthenticationForm(request, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user.is_staff:
            login(request, user)
            log_security_event('admin_login', f'Admin login successful', user=user, request=request)
            messages.success(request, '✅ Admin login successful.')
            return redirect('admin_overview')
        else:
            log_security_event('admin_login_denied', f'Non-staff login attempt', request=request)
            messages.error(request, '❌ Admin access only. Staff credentials required.')

    return render(request, 'core/admin_login.html', {'form': form})


@login_required
def dashboard(request):
    return render(request, 'core/temporarily_unavailable.html', {
        'title': 'Dashboard Temporarily Unavailable',
        'message': 'The user dashboard is currently disabled. Please check back later.',
    }, status=503)


@login_required
def profile_view(request):
    """Display user profile information (read-only)."""
    return render(request, 'core/temporarily_unavailable.html', {
        'title': 'Profile Temporarily Unavailable',
        'message': 'User profiles are currently disabled. Please check back later.',
    }, status=503)


@user_passes_test(_staff_required, login_url='/admin')
def admin_dashboard(request):
    from django.utils import timezone as tz
    from datetime import timedelta
    week_ago = tz.now() - timedelta(days=7)
    pending = Alternative.objects.filter(status='pending').select_related('product', 'added_by').order_by('created_at')
    stats = {
        'pending': Alternative.objects.filter(status='pending').count(),
        'approved_week': Alternative.objects.filter(status='approved', reviewed_at__gte=week_ago).count(),
        'rejected_week': Alternative.objects.filter(status='rejected', reviewed_at__gte=week_ago).count(),
        'needs_changes': Alternative.objects.filter(status='needs_changes').count(),
        'total': Alternative.objects.count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_categories': Category.objects.filter(is_active=True).count(),
        'total_subcategories': SubCategory.objects.filter(is_active=True).count(),
    }
    pending_suggestions = ProductSuggestion.objects.filter(status='pending').select_related('subcategory__category', 'submitted_by').order_by('created_at')
    suggestion_counts = {
        'pending': ProductSuggestion.objects.filter(status='pending').count(),
        'approved': ProductSuggestion.objects.filter(status='approved').count(),
        'rejected': ProductSuggestion.objects.filter(status='rejected').count(),
    }
    pending_reports = Report.objects.filter(status='pending').select_related('product', 'alternative', 'reported_by').order_by('created_at')
    stats['pending_suggestions'] = suggestion_counts['pending']
    stats['pending_reports'] = pending_reports.count()
    return render(request, 'core/admin_dashboard.html', {
        'pending': pending,
        'stats': stats,
        'pending_suggestions': pending_suggestions,
        'suggestion_counts': suggestion_counts,
        'pending_reports': pending_reports,
    })


@user_passes_test(_staff_required, login_url='/admin')
def moderate_alternative(request, pk):
    try:
        alt = get_object_or_404(Alternative, pk=pk)
    except Http404:
        return render(request, 'core/404.html', status=404)
    old_status = alt.status
    form = ModerationForm(instance=alt)

    if request.method == 'POST':
        action = request.POST.get('action')
        form = ModerationForm(request.POST, instance=alt)
        if form.is_valid():
            alt = form.save(commit=False)
            if action in ('approve', 'reject', 'needs_changes'):
                alt.status = 'approved' if action == 'approve' else ('rejected' if action == 'reject' else 'needs_changes')
                alt.reviewed_by = request.user
                alt.reviewed_at = timezone.now()
            alt.save()

            messages.success(request, f'✅ Submission {alt.status}.')
            return redirect('admin_dashboard')

    return render(request, 'core/moderate.html', {'alt': alt, 'form': form})


@rate_limit(key_prefix='forgot_password', limit=5, period=300)
def forgot_password_view(request):
    return render(request, 'core/temporarily_unavailable.html', {
        'title': 'Password Reset Temporarily Unavailable',
        'message': 'Password reset is currently disabled. Please contact an administrator.',
    }, status=503)


def verify_security_view(request):
    return render(request, 'core/temporarily_unavailable.html', {
        'title': 'Password Reset Temporarily Unavailable',
        'message': 'Password reset is currently disabled. Please contact an administrator.',
    }, status=503)


def reset_password_view(request):
    return render(request, 'core/temporarily_unavailable.html', {
        'title': 'Password Reset Temporarily Unavailable',
        'message': 'Password reset is currently disabled. Please contact an administrator.',
    }, status=503)


@login_required
def settings_view(request):
    return render(request, 'core/temporarily_unavailable.html', {
        'title': 'Settings Temporarily Unavailable',
        'message': 'Account settings are currently disabled. Please check back later.',
    }, status=503)


@require_POST
def report_item(request):
    reason = request.POST.get('reason', '').strip()
    details = request.POST.get('details', '').strip()
    product_id = request.POST.get('product_id')
    alternative_id = request.POST.get('alternative_id')

    if not reason:
        return JsonResponse({'error': 'Reason is required.'}, status=400)
    if not product_id and not alternative_id:
        return JsonResponse({'error': 'No target specified.'}, status=400)

    report = Report(reason=reason, details=details)
    if request.user.is_authenticated:
        report.reported_by = request.user
    else:
        report.reporter_name = request.POST.get('reporter_name', '').strip()

    if alternative_id:
        try:
            report.alternative = Alternative.objects.get(pk=alternative_id, status='approved', is_active=True)
        except Alternative.DoesNotExist:
            return JsonResponse({'error': 'Alternative not found.'}, status=404)
    elif product_id:
        try:
            report.product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found.'}, status=404)

    report.save()
    return JsonResponse({'ok': True})


@require_POST
def delete_account(request):
    return render(request, 'core/temporarily_unavailable.html', {
        'title': 'Account Deletion Temporarily Unavailable',
        'message': 'Account deletion is currently disabled. Please check back later.',
    }, status=503)