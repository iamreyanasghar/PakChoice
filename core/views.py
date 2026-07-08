from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, F, Count
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .models import Category, SubCategory, BoycottProduct, PakistaniAlternative, AlternativeVote, UserProfile
from .forms import RegisterForm, LoginForm, AlternativeForm, AvatarForm, ProfileSettingsForm, PasswordChangeForm, ModerationForm


def _staff_required(user):
    return user.is_active and user.is_staff


def home(request):
    categories = Category.objects.prefetch_related('subcategories').all()
    total_products = BoycottProduct.objects.filter(verified=True).count()
    total_alternatives = PakistaniAlternative.objects.filter(status='approved').count()
    return render(request, 'core/home.html', {
        'categories': categories,
        'total_products': total_products,
        'total_alternatives': total_alternatives,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    subcategories = category.subcategories.prefetch_related('products').all()
    return render(request, 'core/category.html', {'category': category, 'subcategories': subcategories})


def subcategory_detail(request, cat_slug, sub_slug):
    category = get_object_or_404(Category, slug=cat_slug)
    subcategory = get_object_or_404(SubCategory, category=category, slug=sub_slug)
    products = subcategory.products.filter(verified=True).prefetch_related('alternatives')
    return render(request, 'core/subcategory.html', {
        'category': category, 'subcategory': subcategory, 'products': products
    })


def product_detail(request, slug):
    product = get_object_or_404(BoycottProduct, slug=slug)
    alternatives = product.alternatives.filter(status='approved')
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


@login_required
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


@login_required
@require_POST
def upvote_alternative(request, pk):
    alt = get_object_or_404(PakistaniAlternative, pk=pk, status='approved')
    vote, created = AlternativeVote.objects.get_or_create(user=request.user, alternative=alt)
    if created:
        PakistaniAlternative.objects.filter(pk=pk).update(upvotes=F('upvotes') + 1)
        alt.refresh_from_db(fields=['upvotes'])
        return JsonResponse({'upvotes': alt.upvotes, 'voted': True})
    vote.delete()
    PakistaniAlternative.objects.filter(pk=pk).update(upvotes=F('upvotes') - 1)
    alt.refresh_from_db(fields=['upvotes'])
    return JsonResponse({'upvotes': max(0, alt.upvotes), 'voted': False})


def search(request):
    q = request.GET.get('q', '').strip()
    products, categories, subcategories = [], [], []
    if q:
        products = list(BoycottProduct.objects.filter(
            Q(name__icontains=q) | Q(brand__icontains=q) | Q(reason__icontains=q)
        ).select_related('subcategory__category')[:20])
        categories = list(Category.objects.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )[:10])
        subcategories = list(SubCategory.objects.filter(
            Q(name__icontains=q) | Q(category__name__icontains=q)
        ).select_related('category')[:10])
    return render(request, 'core/search.html', {
        'products': products,
        'categories': categories,
        'subcategories': subcategories,
        'query': q,
        'total': len(products) + len(categories) + len(subcategories),
        'suggestions': ['Food', 'Beverages', 'Clothing', 'Electronics', 'Coca-Cola', 'Nike', 'Nestlé', 'Pampers', 'Starbucks', 'Zara'],
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        # Save display_name to profile (signal already created the profile)
        display_name = form.cleaned_data.get('display_name', '').strip()
        if display_name:
            user.profile.display_name = display_name
            user.profile.save()
        login(request, user)
        messages.success(request, '✅ Account created! Welcome aboard.')
        return redirect('home')
    return render(request, 'core/auth.html', {'form': form, 'mode': 'register'})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = LoginForm(request, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, '✅ Logged in successfully. Welcome back!')
        next_url = request.POST.get('next') or request.GET.get('next', '')
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('home')
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
            avatar_form = AvatarForm(request.POST, request.FILES, instance=profile)
            if avatar_form.is_valid():
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

    return render(request, 'core/settings.html', {
        'profile_form': profile_form,
        'avatar_form': avatar_form,
        'password_form': password_form,
        'profile': profile,
    })


@login_required
@require_POST
def delete_account(request):
    user = request.user
    logout(request)
    user.delete()
    messages.success(request, 'Your account has been deleted.')
    return redirect('home')
