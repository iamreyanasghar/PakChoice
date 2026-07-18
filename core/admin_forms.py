"""
ModelForms for the custom admin panel.
Used by admin_views.py for validated CRUD operations.
"""
from django import forms
from .models import Category, SubCategory, BoycottProduct, PakistaniAlternative, User, UserProfile


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'icon', 'description', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Category name'}),
            'slug': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'category-slug'}),
            'icon': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '📦', 'maxlength': '10'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Description'}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
        }


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['category', 'name', 'slug', 'icon']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Subcategory name'}),
            'slug': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'subcategory-slug'}),
            'icon': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '📦', 'maxlength': '10'}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = BoycottProduct
        fields = ['subcategory', 'name', 'slug', 'brand', 'country_of_origin', 'reason', 'image_url', 'logo_url', 'verified']
        widgets = {
            'subcategory': forms.Select(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Product name'}),
            'slug': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'product-slug'}),
            'brand': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Brand name'}),
            'country_of_origin': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Country of origin'}),
            'reason': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Reason for boycott'}),
            'image_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'logo_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'verified': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class AlternativeModerationForm(forms.ModelForm):
    class Meta:
        model = PakistaniAlternative
        fields = ['name', 'brand', 'description', 'image_url', 'website', 'admin_notes', 'rejection_reason']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Alternative name'}),
            'brand': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Brand name'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Description'}),
            'image_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'website': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Internal notes (not shown to user)'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Reason shown to the submitter'}),
        }


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['display_name']
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Display name'}),
        }
