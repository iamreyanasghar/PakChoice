from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f'Profile of {self.user.username}'

    def get_display_name(self):
        return self.display_name or self.user.username

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Category(models.Model):
    ICONS = {
        'food': '🍔', 'beverages': '☕', 'personal_care': '🧴', 'household': '🏠',
        'clothing': '👕', 'electronics': '📱', 'baby': '👶', 'health': '💊',
        'snacks': '🍿', 'dairy': '🥛', 'cleaning': '🧹', 'cosmetics': '💄',
    }
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10, default='📦')
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    icon = models.CharField(max_length=10, default='📦')

    class Meta:
        unique_together = ('category', 'slug')
        ordering = ['name']

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class BoycottProduct(models.Model):
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    brand = models.CharField(max_length=200)
    country_of_origin = models.CharField(max_length=100, default='Israel')
    reason = models.TextField()
    image_url = models.URLField(blank=True)
    logo_url = models.URLField(blank=True)
    verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PakistaniAlternative(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_changes', 'Needs Changes'),
    ]
    product = models.ForeignKey(BoycottProduct, on_delete=models.CASCADE, related_name='alternatives')
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    website = models.URLField(blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_alternatives')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    upvotes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # Moderation fields
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_alternatives')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, help_text='Internal notes visible only to admins')
    rejection_reason = models.TextField(blank=True, help_text='Shown to the submitter when rejected or needs changes')

    class Meta:
        ordering = ['-upvotes', 'name']

    def __str__(self):
        return f"{self.name} (alt for {self.product.name})"

    def is_visible(self):
        return self.status == 'approved'


class AlternativeVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    alternative = models.ForeignKey(PakistaniAlternative, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'alternative')
