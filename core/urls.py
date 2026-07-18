from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    # ── Admin Panel (must come BEFORE slug catch-all) ────
    path('admin-panel/', admin_views.admin_overview, name='admin_overview'),
    path('admin-panel/categories/', admin_views.admin_category_list, name='admin_category_list'),
    path('admin-panel/categories/create/', admin_views.admin_category_create, name='admin_category_create'),
    path('admin-panel/categories/<int:pk>/edit/', admin_views.admin_category_edit, name='admin_category_edit'),
    path('admin-panel/categories/<int:pk>/delete/', admin_views.admin_category_delete, name='admin_category_delete'),
    path('admin-panel/subcategories/', admin_views.admin_subcategory_list, name='admin_subcategory_list'),
    path('admin-panel/subcategories/create/', admin_views.admin_subcategory_create, name='admin_subcategory_create'),
    path('admin-panel/subcategories/<int:pk>/edit/', admin_views.admin_subcategory_edit, name='admin_subcategory_edit'),
    path('admin-panel/subcategories/<int:pk>/delete/', admin_views.admin_subcategory_delete, name='admin_subcategory_delete'),
    path('admin-panel/products/', admin_views.admin_product_list, name='admin_product_list'),
    path('admin-panel/products/create/', admin_views.admin_product_create, name='admin_product_create'),
    path('admin-panel/products/<int:pk>/edit/', admin_views.admin_product_edit, name='admin_product_edit'),
    path('admin-panel/products/<int:pk>/delete/', admin_views.admin_product_delete, name='admin_product_delete'),
    path('admin-panel/alternatives/', admin_views.admin_alternative_list, name='admin_alternative_list'),
    path('admin-panel/alternatives/<int:pk>/delete/', admin_views.admin_alternative_delete, name='admin_alternative_delete'),
    path('admin-panel/users/', admin_views.admin_user_list, name='admin_user_list'),
    path('admin-panel/users/<int:pk>/edit/', admin_views.admin_user_edit, name='admin_user_edit'),
    path('admin-panel/users/<int:pk>/toggle-staff/', admin_views.admin_user_toggle_staff, name='admin_user_toggle_staff'),
    path('admin-panel/users/<int:pk>/delete/', admin_views.admin_user_delete, name='admin_user_delete'),

    # Trash
    path('admin-panel/trash/', admin_views.admin_trash, name='admin_trash'),
    path('admin-panel/trash/<str:model_type>/', admin_views.admin_trash_list, name='admin_trash_list'),
    path('admin-panel/trash/<str:model_type>/<int:pk>/restore/', admin_views.admin_trash_restore, name='admin_trash_restore'),
    path('admin-panel/trash/<str:model_type>/<int:pk>/purge/', admin_views.admin_trash_purge, name='admin_trash_purge'),
    path('admin-panel/trash/<str:model_type>/purge-all/', admin_views.admin_trash_purge_all, name='admin_trash_purge_all'),

    # Public
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('upvote/<int:pk>/', views.upvote_alternative, name='upvote'),

    # Account
    path('account/profile/', views.profile_view, name='profile'),
    path('account/dashboard/', views.dashboard, name='dashboard'),
    path('account/settings/', views.settings_view, name='settings'),
    path('account/delete/', views.delete_account, name='delete_account'),

    # Password Reset
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-security/', views.verify_security_view, name='verify_security'),
    path('reset-password/', views.reset_password_view, name='reset_password'),

    # Moderation
    path('admin-panel/moderation/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/moderation/<int:pk>/', views.moderate_alternative, name='moderate_alternative'),

    # Products & Categories (slug patterns must be LAST)
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('product/<slug:slug>/add-alternative/', views.add_alternative, name='add_alternative'),
    path('<slug:slug>/', views.category_detail, name='category_detail'),
    path('<slug:cat_slug>/<slug:sub_slug>/', views.subcategory_detail, name='subcategory_detail'),
]