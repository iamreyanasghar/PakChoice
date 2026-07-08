from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('upvote/<int:pk>/', views.upvote_alternative, name='upvote'),
    path('account/dashboard/', views.dashboard, name='dashboard'),
    path('account/settings/', views.settings_view, name='settings'),
    path('account/delete/', views.delete_account, name='delete_account'),
    path('moderation/', views.admin_dashboard, name='admin_dashboard'),
    path('moderation/<int:pk>/', views.moderate_alternative, name='moderate_alternative'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('product/<slug:slug>/add-alternative/', views.add_alternative, name='add_alternative'),
    path('<slug:slug>/', views.category_detail, name='category_detail'),
    path('<slug:cat_slug>/<slug:sub_slug>/', views.subcategory_detail, name='subcategory_detail'),
]
