import os
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth import login, logout, update_session_auth_hash, get_user_model
User = get_user_model()
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, F, Count
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .decorators import rate_limit
from .security_logger import log_security_event
from .models import Category, SubCategory, BoycottProduct, PakistaniAlternative, AlternativeVote, UserProfile
from .forms import RegisterForm, LoginForm, AlternativeForm, AvatarForm, ProfileSettingsForm, PasswordChangeForm, ModerationForm, ForgotPasswordForm, VerifySecurityForm, ResetPasswordForm, SecuritySettingsForm


def _staff_required(user):
    return user.is_active and user.is_staff


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
    for product in BoycottProduct.objects.filter(verified=True, is_active=True):
        urls.append({
            'loc': request.build_absolute_uri(reverse('product_detail', args=[product.slug])),
            'priority': '0.5',
            'changefreq': 'weekly',
            'lastmod': product.updated_at.isoformat() if product.updated_at else timezone.now().isoformat(),
        })
    
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url in urls:
        xml.append('  <url>')
        xml.append(f'    <loc>{url["loc"]}</loc>')
        if 'lastmod' in url:
            xml.append(f'    <lastmod>{url["lastmod"]}</lastmod>')
        xml.append(f'    <changefreq>{url["changefreq"]}</changefreq>')
        xml.append(f'    <priority>{url["priority"]}</priority>')
        xml.append('  </url>')
    xml.append('</urlset>')
    
    return HttpResponse('\n'.join(xml), content_type='application/xml')


def home(request):
    categories = Category.objects.filter(is_active=True).annotate(
        subcategory_count=Count('subcategories')
    ).prefetch_related('subcategories').all()
    total_products = BoycottProduct.objects.filter(verified=True, is_active=True).count()
    total_alternatives = PakistaniAlternative.objects.filter(status='approved', is_active=True).count()
    return render(request, 'core/home.html', {
        'categories': categories,
        'total_products': total_products,
        'total_alternatives': total_alternatives,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    subcategories = category.subcategories.filter(is_active=True).annotate(
        product_count=Count('products')
    ).prefetch_related('products').all()
    return render(request, 'core/category.html', {'category': category, 'subcategories': subcategories})


def subcategory_detail(request, cat_slug, sub_slug):
    category = get_object_or_404(Category, slug=cat_slug, is_active=True)
    subcategory = get_object_or_404(SubCategory, category=category, slug=sub_slug, is_active=True)
    products = subcategory.products.filter(verified=True, is_active=True).annotate(
        alternative_count=Count('alternatives')
    ).prefetch_related('alternatives')
    return render(request, 'core/subcategory.html', {
        'category': category, 'subcategory': subcategory, 'products': products
    })


def product_detail(request, slug):
    product = get_object_or_404(BoycottProduct, slug=slug, is_active=True)
    alternatives = product.alternatives.filter(status='approved', is_active=True)
    user_votes = set()
    if request.user.is_authenticated:
        user_votes = set(AlternativeVote.objects.filter(
            user=request.user, alternative__in=alternatives
        ).values_list('alternative_id', flat=True))
    form = AlternativeForm()
    return render(request, 'core/product.html', {
        'product': product, 'alternatives': alternatives,
        'form': form, 'user_votes': user_votes,
    })


@require_POST
def add_alternative(request, slug):
    product = get_object_or_404(BoycottProduct, slug=slug)
    form = AlternativeForm(request.POST)
    if form.is_valid():
        alt = form.save(commit=False)
        alt.product = product
        alt.added_by = request.user
        alt.status = 'pending'
        alt.save()
        messages.success(request, '✅ Alternative submitted! It will appear after admin review.')
    else:
        for error in form.errors.values():
            messages.error(request, error[0])
    return redirect('product_detail', slug=slug)


@require_POST
@login_required
@rate_limit(key_prefix='upvote', limit=30, period=60)
def upvote_alternative(request, pk):
    alt = get_object_or_404(PakistaniAlternative, pk=pk, status='approved')
    with transaction.atomic():
        alt = PakistaniAlternative.objects.select_for_update().get(pk=pk)
        existing_vote = AlternativeVote.objects.filter(
            user=request.user, alternative=alt
        ).first()
        if existing_vote:
            existing_vote.delete()
            alt.upvotes = F('upvotes') - 1
            voted = False
        else:
            AlternativeVote.objects.create(user=request.user, alternative=alt)
            alt.upvotes = F('upvotes') + 1
            voted = True
        alt.save()
        alt.refresh_from_db(fields=['upvotes'])
    return JsonResponse({'upvotes': max(0, alt.upvotes), 'voted': voted})


from django.core.paginator import Paginator


def search(request):
    q = request.GET.get('q', '').strip()
    products, categories, subcategories = [], [], []
    product_page = request.GET.get('product_page', 1)
    category_page = request.GET.get('category_page', 1)
    subcategory_page = request.GET.get('subcategory_page', 1)

    if q:
        products_qs = BoycottProduct.objects.filter(
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

    # Dynamic suggestions from popular categories and products
    suggestions = list(Category.objects.filter(is_active=True).order_by('order')[:6].values_list('name', flat=True))
    popular_products = list(BoycottProduct.objects.filter(verified=True, is_active=True).order_by('name')[:4].values_list('name', flat=True))
    suggestions.extend(popular_products)

    total = 0
    if products:
        total += products.paginator.count
    if categories:
        total += categories.paginator.count
    if subcategories:
        total += subcategories.paginator.count

    return render(request, 'core/search.html', {
        'products': products,
        'categories': categories,
        'subcategories': subcategories,
        'query': q,
        'total': total,
        'suggestions': suggestions[:10],
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()

        # Save profile data (signal already created the profile)
        profile = user.profile
        profile.security_question = form.cleaned_data.get('security_question', '')
        profile.set_security_answer(form.cleaned_data.get('security_answer', ''))
        display_name = form.cleaned_data.get('display_name', '').strip()
        if display_name:
            profile.display_name = display_name
        profile.save()

        # Log the user in and redirect to dashboard
        login(request, user)
        messages.success(request, '✅ Account created successfully! Welcome to PakChoice.')
        return redirect('dashboard')

    return render(request, 'core/auth.html', {'form': form, 'mode': 'register'})


@rate_limit(key_prefix='login', limit=5, period=300)
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        log_security_event('login_success', f'User {user.username} logged in successfully', user=user, request=request)
        messages.success(request, '✅ Logged in successfully. Welcome back!')
        next_url = request.POST.get('next') or request.GET.get('next', '')
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('dashboard')
    
    if request.method == 'POST':
        log_security_event('login_failed', 'Failed login attempt', request=request)
    
    return render(request, 'core/auth.html', {'form': form, 'mode': 'login'})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    alternatives = PakistaniAlternative.objects.filter(
        added_by=request.user
    ).select_related('product__subcategory__category').order_by('-created_at')
    votes = AlternativeVote.objects.filter(
        user=request.user
    ).select_related('alternative__product').order_by('-alternative__created_at')
    return render(request, 'core/dashboard.html', {
        'alternatives': alternatives,
        'votes': votes,
    })


@login_required
def profile_view(request):
    """Display user profile information (read-only)."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'core/profile.html', {
        'profile': profile,
    })


@user_passes_test(_staff_required, login_url='/login/')
def admin_dashboard(request):
    from django.utils import timezone as tz
    from datetime import timedelta
    week_ago = tz.now() - timedelta(days=7)
    pending = PakistaniAlternative.objects.filter(status='pending').select_related('product', 'added_by').order_by('created_at')
    stats = {
        'pending': PakistaniAlternative.objects.filter(status='pending').count(),
        'approved_week': PakistaniAlternative.objects.filter(status='approved', reviewed_at__gte=week_ago).count(),
        'rejected_week': PakistaniAlternative.objects.filter(status='rejected', reviewed_at__gte=week_ago).count(),
        'needs_changes': PakistaniAlternative.objects.filter(status='needs_changes').count(),
        'total': PakistaniAlternative.objects.count(),
    }
    return render(request, 'core/admin_dashboard.html', {'pending': pending, 'stats': stats})


@user_passes_test(_staff_required, login_url='/login/')
def moderate_alternative(request, pk):
    alt = get_object_or_404(PakistaniAlternative, pk=pk)
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
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    form = ForgotPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
            if not user.profile.security_question:
                messages.error(request, 'No security question set for this account. Please contact support.')
                return redirect('forgot_password')
            request.session['reset_username'] = username
            return redirect('verify_security')
        except User.DoesNotExist:
            messages.error(request, 'No account found with that username.')
    
    return render(request, 'core/forgot_password.html', {'form': form})


def verify_security_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    username = request.session.get('reset_username')
    if not username:
        messages.error(request, 'Please start the password reset process first.')
        return redirect('forgot_password')
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'Invalid session. Please try again.')
        return redirect('forgot_password')
    
    form = VerifySecurityForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if user.profile.check_security_answer(form.cleaned_data['security_answer']):
            request.session['security_verified'] = True
            return redirect('reset_password')
        else:
            messages.error(request, 'Incorrect security answer. Please try again.')
    
    question_display = dict(UserProfile.SECURITY_QUESTIONS).get(user.profile.security_question, 'Security Question')
    return render(request, 'core/verify_security.html', {
        'form': form,
        'question': question_display,
    })


def reset_password_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if not request.session.get('security_verified'):
        messages.error(request, 'Please verify your security question first.')
        return redirect('forgot_password')
    
    form = ResetPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = request.session.get('reset_username')
        try:
            user = User.objects.get(username=username)
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            # Clear session
            request.session.pop('reset_username', None)
            request.session.pop('security_verified', None)
            log_security_event('password_reset', f'Password reset successful for user {user.username}', user=user, request=request)
            messages.success(request, '✅ Password reset successful! You can now log in with your new password.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'Invalid session. Please try again.')
            return redirect('forgot_password')
    
    return render(request, 'core/reset_password.html', {'form': form})


@login_required
def settings_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    profile_form = ProfileSettingsForm(request.user, instance=profile)
    avatar_form = AvatarForm(instance=profile)
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'profile':
            profile_form = ProfileSettingsForm(request.user, request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, '✅ Profile updated successfully.')
                return redirect('settings')

        elif action == 'avatar':
            if request.POST.get('remove_avatar'):
                if profile.avatar:
                    old_file = profile.avatar.path if hasattr(profile.avatar, 'path') else None
                    profile.avatar = None
                    profile.save()
                    if old_file and os.path.exists(old_file):
                        os.remove(old_file)
                    messages.success(request, '✅ Avatar removed successfully.')
                return redirect('settings')
            avatar_form = AvatarForm(request.POST, request.FILES, instance=profile)
            if avatar_form.is_valid():
                if profile.avatar:
                    old_file = profile.avatar.path if hasattr(profile.avatar, 'path') else None
                    avatar_form.save()
                    if old_file and os.path.exists(old_file):
                        os.remove(old_file)
                else:
                    avatar_form.save()
                messages.success(request, '✅ Avatar updated successfully.')
                return redirect('settings')

        elif action == 'password':
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, '✅ Password changed successfully.')
                return redirect('settings')

        elif action == 'security':
            security_form = SecuritySettingsForm(request.POST, instance=profile)
            if security_form.is_valid():
                security_form.save()
                messages.success(request, '✅ Security settings updated successfully.')
                return redirect('settings')

    security_form = SecuritySettingsForm(instance=profile)
    return render(request, 'core/settings.html', {
        'profile_form': profile_form,
        'avatar_form': avatar_form,
        'password_form': password_form,
        'security_form': security_form,
        'profile': profile,
    })


@require_POST
def delete_account(request):
    from django.contrib.auth import authenticate
    
    user = request.user
    confirm_password = request.POST.get('confirm_password', '')
    
    # Verify password
    if not confirm_password:
        log_security_event('account_delete_failed', f'Account deletion attempt without password for user {user.username}', user=user, request=request)
        messages.error(request, 'Please enter your password to confirm account deletion.')
        return redirect('settings')
    
    authenticated_user = authenticate(request, username=user.username, password=confirm_password)
    if authenticated_user is None:
        log_security_event('account_delete_failed', f'Account deletion attempt with wrong password for user {user.username}', user=user, request=request)
        messages.error(request, 'Incorrect password. Account deletion cancelled.')
        return redirect('settings')
    
    username = user.username
    logout(request)
    user.delete()
    log_security_event('account_deleted', f'Account deleted for user {username}', request=request)
    messages.success(request, 'Your account has been deleted.')
    return redirect('home')