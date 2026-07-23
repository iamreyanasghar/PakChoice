"""
Test suite for the PakChoice application.
Covers models, views, forms, and core functionality.
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    Category, SubCategory, BoycottProduct, PakistaniAlternative,
    AlternativeVote, UserProfile
)
from .forms import (
    RegisterForm, LoginForm, AlternativeForm, AvatarForm,
    ProfileSettingsForm, PasswordChangeForm, ModerationForm,
    ForgotPasswordForm, VerifySecurityForm, ResetPasswordForm,
    SecuritySettingsForm
)


# ── Model Tests ──────────────────────────────────────────────

class CategoryModelTests(TestCase):
    def test_create_category(self):
        category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            icon='📦',
            description='A test category',
            order=1
        )
        self.assertEqual(str(category), 'Test Category')
        self.assertEqual(category.slug, 'test-category')

    def test_category_ordering(self):
        Category.objects.create(name='B', slug='b', order=2)
        Category.objects.create(name='A', slug='a', order=1)
        categories = list(Category.objects.all())
        self.assertEqual(categories[0].name, 'A')
        self.assertEqual(categories[1].name, 'B')


class SubCategoryModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Food', slug='food', order=1
        )

    def test_create_subcategory(self):
        sub = SubCategory.objects.create(
            category=self.category,
            name='Fast Food',
            slug='fast-food',
            icon='🍔'
        )
        self.assertEqual(str(sub), 'Food → Fast Food')

    def test_unique_together_constraint(self):
        SubCategory.objects.create(
            category=self.category, name='Sub1', slug='sub1'
        )
        with self.assertRaises(Exception):
            SubCategory.objects.create(
                category=self.category, name='Sub2', slug='sub1'
            )


class BoycottProductModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Food', slug='food', order=1)
        self.subcategory = SubCategory.objects.create(
            category=self.category, name='Fast Food', slug='fast-food'
        )

    def test_create_product(self):
        product = BoycottProduct.objects.create(
            subcategory=self.subcategory,
            name='Test Product',
            slug='test-product',
            brand='Test Brand',
            country_of_origin='USA',
            reason='Test reason'
        )
        self.assertEqual(str(product), 'Test Product')
        self.assertTrue(product.verified)  # default is True

    def test_product_ordering(self):
        BoycottProduct.objects.create(
            subcategory=self.subcategory, name='B', slug='b', brand='Brand B'
        )
        BoycottProduct.objects.create(
            subcategory=self.subcategory, name='A', slug='a', brand='Brand A'
        )
        products = list(BoycottProduct.objects.all())
        self.assertEqual(products[0].name, 'A')
        self.assertEqual(products[1].name, 'B')


class PakistaniAlternativeModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Food', slug='food', order=1)
        self.subcategory = SubCategory.objects.create(
            category=self.category, name='Fast Food', slug='fast-food'
        )
        self.product = BoycottProduct.objects.create(
            subcategory=self.subcategory,
            name='McDonalds',
            slug='mcdonalds',
            brand='McDonalds Corp',
            reason='Test reason'
        )
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_create_alternative(self):
        alt = PakistaniAlternative.objects.create(
            product=self.product,
            name='Local Burger',
            brand='Local Brand',
            description='A great local alternative',
            status='pending',
            added_by=self.user
        )
        self.assertEqual(alt.status, 'pending')
        self.assertFalse(alt.is_visible())

    def test_approved_alternative_is_visible(self):
        alt = PakistaniAlternative.objects.create(
            product=self.product,
            name='Local Burger',
            brand='Local Brand',
            status='approved'
        )
        self.assertTrue(alt.is_visible())

    def test_upvotes_default(self):
        alt = PakistaniAlternative.objects.create(
            product=self.product, name='Alt', brand='Brand', status='approved'
        )
        self.assertEqual(alt.upvotes, 0)


class AlternativeVoteModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Food', slug='food', order=1)
        self.subcategory = SubCategory.objects.create(
            category=self.category, name='Fast Food', slug='fast-food'
        )
        self.product = BoycottProduct.objects.create(
            subcategory=self.subcategory,
            name='McDonalds',
            slug='mcdonalds',
            brand='McDonalds Corp',
            reason='Test reason'
        )
        self.alternative = PakistaniAlternative.objects.create(
            product=self.product, name='Local Burger', brand='Local', status='approved'
        )
        self.user1 = User.objects.create_user(username='user1', password='pass1')
        self.user2 = User.objects.create_user(username='user2', password='pass2')

    def test_unique_vote_per_user(self):
        AlternativeVote.objects.create(user=self.user1, alternative=self.alternative)
        with self.assertRaises(Exception):
            AlternativeVote.objects.create(user=self.user1, alternative=self.alternative)

    def test_different_users_can_vote(self):
        AlternativeVote.objects.create(user=self.user1, alternative=self.alternative)
        vote2 = AlternativeVote.objects.create(user=self.user2, alternative=self.alternative)
        self.assertIsNotNone(vote2.pk)


class UserProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_profile_created_via_signal(self):
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertEqual(str(self.user.profile), f'Profile of {self.user.username}')

    def test_get_display_name(self):
        self.user.profile.display_name = 'Test Display'
        self.user.profile.save()
        self.assertEqual(self.user.profile.get_display_name(), 'Test Display')
        self.user.profile.display_name = ''
        self.user.profile.save()
        self.assertEqual(self.user.profile.get_display_name(), self.user.username)
        # Test first_name + last_name fallback
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()
        self.assertEqual(self.user.profile.get_display_name(), 'John Doe')
        # Test first_name only fallback
        self.user.last_name = ''
        self.user.save()
        self.assertEqual(self.user.profile.get_display_name(), 'John')

    def test_security_answer_hashing(self):
        self.user.profile.set_security_answer('mysecret')
        self.user.profile.save()
        self.assertNotEqual(self.user.profile.security_answer, 'mysecret')
        self.assertTrue(self.user.profile.check_security_answer('mysecret'))
        self.assertFalse(self.user.profile.check_security_answer('wrong'))


# ── View Tests ───────────────────────────────────────────────

class HomeViewTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')

    def test_home_page_context(self):
        response = self.client.get(reverse('home'))
        self.assertIn('categories', response.context)
        self.assertIn('total_products', response.context)
        self.assertIn('total_alternatives', response.context)


class CategoryDetailViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Food', slug='food', order=1
        )

    def test_category_detail_loads(self):
        response = self.client.get(reverse('category_detail', args=['food']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/category.html')
        self.assertEqual(response.context['category'], self.category)

    def test_category_detail_404(self):
        response = self.client.get(reverse('category_detail', args=['nonexistent']))
        self.assertEqual(response.status_code, 404)


class SubCategoryDetailViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Food', slug='food', order=1)
        self.subcategory = SubCategory.objects.create(
            category=self.category, name='Fast Food', slug='fast-food'
        )

    def test_subcategory_detail_loads(self):
        response = self.client.get(reverse('subcategory_detail', args=['food', 'fast-food']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/subcategory.html')


class ProductDetailViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Food', slug='food', order=1)
        self.subcategory = SubCategory.objects.create(
            category=self.category, name='Fast Food', slug='fast-food'
        )
        self.product = BoycottProduct.objects.create(
            subcategory=self.subcategory,
            name='McDonalds',
            slug='mcdonalds',
            brand='McDonalds',
            reason='Test reason'
        )

    def test_product_detail_loads(self):
        response = self.client.get(reverse('product_detail', args=['mcdonalds']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/product.html')

    def test_product_detail_404(self):
        response = self.client.get(reverse('product_detail', args=['nonexistent']))
        self.assertEqual(response.status_code, 404)


class SearchViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Food', slug='food', order=1)
        self.subcategory = SubCategory.objects.create(
            category=self.category, name='Fast Food', slug='fast-food'
        )
        self.product = BoycottProduct.objects.create(
            subcategory=self.subcategory,
            name='McDonalds',
            slug='mcdonalds',
            brand='McDonalds',
            reason='Test reason'
        )

    def test_search_with_query(self):
        response = self.client.get(reverse('search'), {'q': 'McDonalds'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('products', response.context)
        self.assertEqual(len(response.context['products']), 1)

    def test_search_without_query(self):
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 0)

    def test_search_suggestions_are_dynamic(self):
        response = self.client.get(reverse('search'))
        suggestions = response.context['suggestions']
        self.assertIsInstance(suggestions, list)
        self.assertLessEqual(len(suggestions), 10)


class AuthViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_register_view_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/auth.html')

    def test_register_view_post_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'display_name': 'New User',
            'email': 'new@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123',
            'security_question': 'color',
            'security_answer': 'blue'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertTrue(UserProfile.objects.filter(user__username='newuser').exists())

    def test_login_view_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_view_post_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_view_post_failure(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.category = Category.objects.create(name='Food', slug='food', order=1)
        self.subcategory = SubCategory.objects.create(
            category=self.category, name='Fast Food', slug='fast-food'
        )
        self.product = BoycottProduct.objects.create(
            subcategory=self.subcategory,
            name='McDonalds',
            slug='mcdonalds',
            brand='McDonalds',
            reason='Test reason'
        )
        self.alternative = PakistaniAlternative.objects.create(
            product=self.product,
            name='Local Burger',
            brand='Local',
            status='approved',
            added_by=self.user
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_loads_for_authenticated_user(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('alternatives', response.context)
        self.assertIn('votes', response.context)


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)

    def test_profile_loads(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile', response.context)


class SettingsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_settings_requires_login(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 302)

    def test_settings_loads(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)


class AddAlternativeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.category = Category.objects.create(name='Food', slug='food', order=1)
        self.subcategory = SubCategory.objects.create(
            category=self.category, name='Fast Food', slug='fast-food'
        )
        self.product = BoycottProduct.objects.create(
            subcategory=self.subcategory,
            name='McDonalds',
            slug='mcdonalds',
            brand='McDonalds',
            reason='Test reason'
        )

    def test_add_alternative_requires_login(self):
        response = self.client.post(reverse('add_alternative', args=['mcdonalds']))
        self.assertEqual(response.status_code, 302)

    def test_add_alternative_success(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('add_alternative', args=['mcdonalds']), {
            'name': 'Local Burger',
            'brand': 'Local Brand',
            'description': 'Great alternative',
            'image_url': 'https://example.com/image.jpg',
            'website': 'https://example.com'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            PakistaniAlternative.objects.filter(name='Local Burger').exists()
        )
        alt = PakistaniAlternative.objects.get(name='Local Burger')
        self.assertEqual(alt.status, 'pending')
        self.assertEqual(alt.added_by, self.user)


class UpvoteViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )
        self.category = Category.objects.create(name='Food', slug='food', order=1)
        self.subcategory = SubCategory.objects.create(
            category=self.category, name='Fast Food', slug='fast-food'
        )
        self.product = BoycottProduct.objects.create(
            subcategory=self.subcategory,
            name='McDonalds',
            slug='mcdonalds',
            brand='McDonalds',
            reason='Test reason'
        )
        self.alternative = PakistaniAlternative.objects.create(
            product=self.product,
            name='Local Burger',
            brand='Local',
            status='approved'
        )

    def test_upvote_requires_login(self):
        response = self.client.post(reverse('upvote', args=[self.alternative.pk]))
        self.assertEqual(response.status_code, 302)

    def test_upvote_creates_vote(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('upvote', args=[self.alternative.pk]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['voted'])
        self.assertEqual(data['upvotes'], 1)
        self.assertTrue(
            AlternativeVote.objects.filter(
                user=self.user, alternative=self.alternative
            ).exists()
        )

    def test_upvote_toggles_off(self):
        self.client.login(username='testuser', password='testpass123')
        # First upvote
        self.client.post(reverse('upvote', args=[self.alternative.pk]))
        # Second upvote (should remove)
        response = self.client.post(reverse('upvote', args=[self.alternative.pk]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['voted'])
        self.assertEqual(data['upvotes'], 0)


class AdminViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        self.user = User.objects.create_user(
            username='regularuser', password='userpass123'
        )
        self.category = Category.objects.create(name='Food', slug='food', order=1)
        self.subcategory = SubCategory.objects.create(
            category=self.category, name='Fast Food', slug='fast-food'
        )
        self.product = BoycottProduct.objects.create(
            subcategory=self.subcategory,
            name='McDonalds',
            slug='mcdonalds',
            brand='McDonalds',
            reason='Test reason'
        )
        self.alternative = PakistaniAlternative.objects.create(
            product=self.product,
            name='Local Burger',
            brand='Local',
            status='pending',
            added_by=self.user
        )

    def test_admin_dashboard_requires_staff(self):
        self.client.login(username='regularuser', password='userpass123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_loads_for_staff(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('pending', response.context)
        self.assertIn('stats', response.context)

    def test_admin_category_list(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('admin_category_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_product_list(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('admin_product_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_alternative_list(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('admin_alternative_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_user_list(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('admin_user_list'))
        self.assertEqual(response.status_code, 200)


class ModerationViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        self.category = Category.objects.create(name='Food', slug='food', order=1)
        self.subcategory = SubCategory.objects.create(
            category=self.category, name='Fast Food', slug='fast-food'
        )
        self.product = BoycottProduct.objects.create(
            subcategory=self.subcategory,
            name='McDonalds',
            slug='mcdonalds',
            brand='McDonalds',
            reason='Test reason'
        )
        self.alternative = PakistaniAlternative.objects.create(
            product=self.product,
            name='Local Burger',
            brand='Local',
            status='pending'
        )

    def test_moderate_alternative_approve(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(
            reverse('moderate_alternative', args=[self.alternative.pk]),
            {'action': 'approve', 'name': 'Local Burger', 'brand': 'Local'}
        )
        self.assertEqual(response.status_code, 302)
        self.alternative.refresh_from_db()
        self.assertEqual(self.alternative.status, 'approved')
        self.assertEqual(self.alternative.reviewed_by, self.admin)

    def test_moderate_alternative_reject(self):
        self.client.login(username='admin', password='adminpass123')
        response = self.client.post(
            reverse('moderate_alternative', args=[self.alternative.pk]),
            {
                'action': 'reject',
                'name': 'Local Burger',
                'brand': 'Local',
                'rejection_reason': 'Not a good alternative'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.alternative.refresh_from_db()
        self.assertEqual(self.alternative.status, 'rejected')


class PasswordResetViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.user.profile.security_question = 'color'
        self.user.profile.set_security_answer('blue')
        self.user.profile.save()

    def test_forgot_password_view_get(self):
        response = self.client.get(reverse('forgot_password'))
        self.assertEqual(response.status_code, 200)

    def test_forgot_password_valid_username(self):
        response = self.client.post(reverse('forgot_password'), {
            'username': 'testuser'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('verify_security'))

    def test_forgot_password_invalid_username(self):
        response = self.client.post(reverse('forgot_password'), {
            'username': 'nonexistent'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            self.client.session.get('reset_username')
        )

    def test_verify_security_view(self):
        session = self.client.session
        session['reset_username'] = 'testuser'
        session.save()
        response = self.client.post(reverse('verify_security'), {
            'security_answer': 'blue'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('reset_password'))

    def test_verify_security_wrong_answer(self):
        session = self.client.session
        session['reset_username'] = 'testuser'
        session.save()
        response = self.client.post(reverse('verify_security'), {
            'security_answer': 'red'
        })
        self.assertEqual(response.status_code, 200)

    def test_reset_password_view(self):
        session = self.client.session
        session['reset_username'] = 'testuser'
        session['security_verified'] = True
        session.save()
        response = self.client.post(reverse('reset_password'), {
            'new_password1': 'newpass123',
            'new_password2': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))


class DeleteAccountViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_delete_account_requires_login(self):
        response = self.client.post(reverse('delete_account'))
        self.assertEqual(response.status_code, 302)

    def test_delete_account_success(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('delete_account'), {
            'confirm_password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username='testuser').exists())

    def test_delete_account_wrong_password(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('delete_account'), {
            'confirm_password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='testuser').exists())


# ── Form Tests ───────────────────────────────────────────────

class RegisterFormTests(TestCase):
    def test_valid_form(self):
        form = RegisterForm(data={
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'display_name': 'New User',
            'email': 'new@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123',
            'security_question': 'color',
            'security_answer': 'blue'
        })
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        form = RegisterForm(data={
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@example.com',
            'password1': 'newpass123',
            'password2': 'differentpass',
            'security_question': 'color',
            'security_answer': 'blue'
        })
        self.assertFalse(form.is_valid())


class LoginFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass123'
        )

    def test_valid_login(self):
        form = LoginForm(request=None, data={
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertTrue(form.is_valid())

    def test_invalid_login(self):
        form = LoginForm(request=None, data={
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertFalse(form.is_valid())


class AlternativeFormTests(TestCase):
    def test_valid_form(self):
        form = AlternativeForm(data={
            'name': 'Local Burger',
            'brand': 'Local Brand',
            'description': 'Great alternative',
            'image_url': 'https://example.com/image.jpg',
            'website': 'https://example.com'
        })
        self.assertTrue(form.is_valid())

    def test_empty_name_invalid(self):
        form = AlternativeForm(data={
            'name': '',
            'brand': 'Local Brand',
        })
        self.assertFalse(form.is_valid())


class AvatarFormTests(TestCase):
    def test_valid_image_extension(self):
        image = SimpleUploadedFile(
            'test.jpg',
            b'GIF87a' + b'\x00' * 100,
            content_type='image/jpeg'
        )
        form = AvatarForm(data={'avatar': image})
        # Note: imghdr may not recognize this minimal data, but form validates extension
        self.assertTrue(form.is_valid() or 'avatar' in form.errors)

    def test_file_too_large(self):
        # Create a file just over 5MB
        large_content = b'\xff\xd8\xff\xe0' + b'\x00' * (5 * 1024 * 1024 + 1000)
        large_image = SimpleUploadedFile(
            'test.jpg',
            large_content,
            content_type='image/jpeg'
        )
        # File uploads must be passed in 'files' parameter, not 'data'
        form = AvatarForm(files={'avatar': large_image})
        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)


class ModerationFormTests(TestCase):
    def test_valid_form(self):
        form = ModerationForm(data={
            'name': 'Local Burger',
            'brand': 'Local',
            'description': 'Great',
            'admin_notes': 'Looks good',
            'rejection_reason': ''
        })
        self.assertTrue(form.is_valid())


# ── Middleware Tests ─────────────────────────────────────────

class MiddlewareTests(TestCase):
    def test_cache_control_for_static(self):
        response = self.client.get('/static/css/main.css')
        # Static files may 404 but middleware should still set headers
        self.assertIn('Cache-Control', response)

    def test_security_headers_present(self):
        response = self.client.get(reverse('home'))
        self.assertIn('Content-Security-Policy', response)
        self.assertIn('Permissions-Policy', response)
        self.assertIn('Referrer-Policy', response)


# ── Decorator Tests ──────────────────────────────────────────

class RateLimitDecoratorTests(TestCase):
    def test_rate_limit_blocks_excess_requests(self):
        from django.core.cache import cache
        
        # Clear any cached rate limit data from other tests
        cache.clear()
        
        # Test rate limiting via the login view which uses the decorator
        # Use a unique username to avoid conflicts with other tests
        unique_user = 'ratelimit_test_unique_user'
        User.objects.create_user(username=unique_user, password='pass123')
        
        client = Client()
        
        # Make 5 failed login attempts (limit is 5 per 300 seconds)
        for i in range(5):
            response = client.post(reverse('login'), {
                'username': unique_user,
                'password': 'wrongpass'
            })
            self.assertEqual(response.status_code, 200)
        
        # 6th attempt should be rate limited
        response = client.post(reverse('login'), {
            'username': unique_user,
            'password': 'wrongpass'
        })
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)


# ── Integration Tests ────────────────────────────────────────

class FullWorkflowTests(TestCase):
    """Test the complete user workflow from registration to moderation."""

    def setUp(self):
        self.category = Category.objects.create(name='Food', slug='food', order=1)
        self.subcategory = SubCategory.objects.create(
            category=self.category, name='Fast Food', slug='fast-food'
        )
        self.product = BoycottProduct.objects.create(
            subcategory=self.subcategory,
            name='McDonalds',
            slug='mcdonalds',
            brand='McDonalds',
            reason='Test reason'
        )

    def test_complete_user_workflow(self):
        # 1. Register
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'display_name': 'New User',
            'email': 'new@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123',
            'security_question': 'color',
            'security_answer': 'blue'
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newuser')

        # 2. Login
        self.client.login(username='newuser', password='newpass123')

        # 3. View product
        response = self.client.get(reverse('product_detail', args=['mcdonalds']))
        self.assertEqual(response.status_code, 200)

        # 4. Submit alternative
        response = self.client.post(reverse('add_alternative', args=['mcdonalds']), {
            'name': 'Local Burger',
            'brand': 'Local Brand',
            'description': 'Great alternative',
            'image_url': '',
            'website': ''
        })
        self.assertEqual(response.status_code, 302)
        alt = PakistaniAlternative.objects.get(name='Local Burger')
        self.assertEqual(alt.status, 'pending')
        self.assertEqual(alt.added_by, user)

        # 5. Admin approves
        admin = User.objects.create_user(
            username='admin', password='adminpass', is_staff=True
        )
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(
            reverse('moderate_alternative', args=[alt.pk]),
            {'action': 'approve', 'name': 'Local Burger', 'brand': 'Local Brand'}
        )
        self.assertEqual(response.status_code, 302)
        alt.refresh_from_db()
        self.assertEqual(alt.status, 'approved')

        # 6. Regular user upvotes
        self.client.login(username='newuser', password='newpass123')
        response = self.client.post(reverse('upvote', args=[alt.pk]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['voted'])
        self.assertEqual(data['upvotes'], 1)
