from django.contrib import admin
from django.utils import timezone
from .models import Category, SubCategory, BoycottProduct, PakistaniAlternative, UserProfile, AlternativeVote


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'avatar')
    search_fields = ('user__username', 'display_name')


class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1


class ProductInline(admin.TabularInline):
    model = BoycottProduct
    extra = 1
    fields = ('name', 'brand', 'verified')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'order')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [SubCategoryInline]


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'icon')
    list_filter = ('category',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductInline]


@admin.register(BoycottProduct)
class BoycottProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'subcategory', 'verified')
    list_filter = ('subcategory__category', 'verified')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'brand')


@admin.action(description='✅ Approve selected alternatives')
def approve_alternatives(modeladmin, request, queryset):
    updated = queryset.exclude(status='approved').update(
        status='approved', reviewed_by=request.user, reviewed_at=timezone.now()
    )
    modeladmin.message_user(request, f'{updated} alternative(s) approved.')


@admin.action(description='❌ Reject selected alternatives')
def reject_alternatives(modeladmin, request, queryset):
    updated = queryset.exclude(status='rejected').update(
        status='rejected', reviewed_by=request.user, reviewed_at=timezone.now()
    )
    modeladmin.message_user(request, f'{updated} alternative(s) rejected.')


@admin.action(description='🔄 Request changes on selected alternatives')
def request_changes(modeladmin, request, queryset):
    updated = queryset.exclude(status='needs_changes').update(
        status='needs_changes', reviewed_by=request.user, reviewed_at=timezone.now()
    )
    modeladmin.message_user(request, f'{updated} alternative(s) marked as needs changes.')


@admin.register(PakistaniAlternative)
class AlternativeAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'product', 'status', 'added_by', 'reviewed_by', 'reviewed_at', 'upvotes')
    list_filter = ('status', 'product__subcategory__category')
    search_fields = ('name', 'brand', 'added_by__username')
    readonly_fields = ('added_by', 'reviewed_by', 'reviewed_at', 'upvotes', 'created_at')
    actions = [approve_alternatives, reject_alternatives, request_changes]
    fieldsets = (
        ('Submission', {'fields': ('product', 'name', 'brand', 'description', 'image_url', 'website', 'added_by', 'created_at')}),
        ('Moderation', {'fields': ('status', 'admin_notes', 'rejection_reason', 'reviewed_by', 'reviewed_at')}),
        ('Stats', {'fields': ('upvotes',)}),
    )

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(AlternativeVote)
class AlternativeVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'alternative', 'alternative_product', 'alternative_brand')
    list_filter = ('alternative__product__subcategory__category',)
    search_fields = ('user__username', 'alternative__name', 'alternative__brand')
    readonly_fields = ('user', 'alternative')

    def alternative_product(self, obj):
        return obj.alternative.product.name
    alternative_product.short_description = 'Product'
    alternative_product.admin_order_field = 'alternative__product__name'

    def alternative_brand(self, obj):
        return obj.alternative.brand
    alternative_brand.short_description = 'Alternative Brand'
    alternative_brand.admin_order_field = 'alternative__brand'
