from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Stock, Employee, Order, Sneaker, CartItem, PaymentSetting
from .promptpay import generate_promptpay_payload


PNG_BYTES = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
    b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)


class PaginationViewTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='admin', password='pass', is_staff=True)
        for i in range(6):
            sneaker = Sneaker.objects.create(
                name=f'Shoe {i}', brand='Nike', size=10, price=1000,
                release_date='2024-01-01',
            )
            Stock.objects.create(sneaker=sneaker, quantity=5, location=f'โกดัง {i}')
            Employee.objects.create(first_name=f'F{i}', last_name=f'L{i}', phone='0812345678')
            Order.objects.create(user=self.staff, first_name='A', last_name='B', address='x', postal_code='10110', phone='0812345678')

    def test_list_pages_render(self):
        client = Client()
        client.force_login(self.staff)
        for url in ['/', '/stock/', '/employees/', '/admin-orders/', '/my-orders/', '/sneakers/', '/profile/']:
            response = client.get(url)
            self.assertEqual(response.status_code, 200, url)


class PermissionTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='admin', password='pass', is_staff=True)
        self.customer = User.objects.create_user(username='user', password='pass', is_staff=False)

    def test_anonymous_cannot_access_protected_pages(self):
        client = Client()
        for url in ['/profile/', '/cart/', '/my-orders/', '/sneakers/', '/admin-orders/']:
            response = client.get(url)
            self.assertEqual(response.status_code, 302, url)

    def test_customer_cannot_access_admin_pages(self):
        client = Client()
        client.force_login(self.customer)
        for url in ['/admin-orders/', '/admin-carts/', '/stock/create/', '/employees/create/']:
            response = client.get(url)
            self.assertEqual(response.status_code, 302, url)

    def test_staff_can_access_admin_pages(self):
        client = Client()
        client.force_login(self.staff)
        for url in ['/admin-orders/', '/admin-carts/', '/stock/', '/employees/']:
            response = client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_regular_user_can_access_profile(self):
        client = Client()
        client.force_login(self.customer)
        response = client.get('/profile/')
        self.assertEqual(response.status_code, 200)

    def test_profile_post_updates_user_and_avatar(self):
        client = Client()
        client.force_login(self.customer)
        response = client.post('/profile/', {
            'username': 'user',
            'first_name': 'สมชาย',
            'last_name': 'ใจดี',
            'email': 'somchai@example.com',
            'avatar': '',
        })
        self.assertEqual(response.status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.first_name, 'สมชาย')
        self.assertEqual(self.customer.email, 'somchai@example.com')


class AdminUserPermissionTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='admin', password='pass', is_staff=True)
        self.member = User.objects.create_user(username='member', password='pass', is_staff=False)
        self.client = Client()
        self.client.force_login(self.staff)

    def test_admin_users_page_accessible(self):
        response = self.client.get('/admin-users/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '@member')

    def test_admin_users_page_denied_for_member(self):
        client = Client()
        client.force_login(self.member)
        response = client.get('/admin-users/')
        self.assertEqual(response.status_code, 302)

    def test_admin_users_page_denied_for_anonymous(self):
        response = Client().get('/admin-users/')
        self.assertEqual(response.status_code, 302)

    def test_promote_member_to_admin(self):
        response = self.client.post(f'/admin-users/role/{self.member.pk}/', {'role': 'admin'})
        self.assertEqual(response.status_code, 302)
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_staff)

    def test_demote_admin_to_member(self):
        other_admin = User.objects.create_user(username='other', password='pass', is_staff=True)
        response = self.client.post(f'/admin-users/role/{other_admin.pk}/', {'role': 'member'})
        self.assertEqual(response.status_code, 302)
        other_admin.refresh_from_db()
        self.assertFalse(other_admin.is_staff)

    def test_cannot_change_own_role(self):
        response = self.client.post(f'/admin-users/role/{self.staff.pk}/', {'role': 'member'})
        self.assertEqual(response.status_code, 302)
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_staff)

    def test_cannot_deactivate_self(self):
        response = self.client.post(f'/admin-users/active/{self.staff.pk}/')
        self.assertEqual(response.status_code, 302)
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_active)

    def test_deactivate_member(self):
        response = self.client.post(f'/admin-users/active/{self.member.pk}/')
        self.assertEqual(response.status_code, 302)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)

    def test_deactivated_member_cannot_login(self):
        self.client.post(f'/admin-users/active/{self.member.pk}/')
        client = Client()
        logged_in = client.login(username='member', password='pass')
        self.assertFalse(logged_in)

    def test_promoted_member_can_access_admin_pages(self):
        self.client.post(f'/admin-users/role/{self.member.pk}/', {'role': 'admin'})
        client = Client()
        client.force_login(self.member)
        response = client.get('/admin-orders/')
        self.assertEqual(response.status_code, 200)

    def test_delete_user_confirm_page(self):
        response = self.client.get(f'/admin-users/delete/{self.member.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '@member')

    def test_delete_user(self):
        response = self.client.post(f'/admin-users/delete/{self.member.pk}/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.member.pk).exists())

    def test_delete_user_cascades_related_data(self):
        from .models import CartItem, Profile, Order
        sneaker = Sneaker.objects.create(
            name='Shoe', brand='Nike', size=10, price=1000, release_date='2024-01-01'
        )
        CartItem.objects.create(user=self.member, sneaker=sneaker)
        Profile.objects.create(user=self.member)
        Order.objects.create(
            user=self.member, first_name='A', last_name='B',
            address='x', postal_code='10110', phone='0812345678'
        )
        self.client.post(f'/admin-users/delete/{self.member.pk}/')
        self.assertFalse(User.objects.filter(pk=self.member.pk).exists())
        self.assertFalse(CartItem.objects.filter(user_id=self.member.pk).exists())
        self.assertFalse(Profile.objects.filter(user_id=self.member.pk).exists())
        self.assertFalse(Order.objects.filter(user_id=self.member.pk).exists())

    def test_cannot_delete_self(self):
        response = self.client.post(f'/admin-users/delete/{self.staff.pk}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(pk=self.staff.pk).exists())

    def test_member_cannot_delete_user(self):
        client = Client()
        client.force_login(self.member)
        staff2 = User.objects.create_user(username='staff2', password='pass', is_staff=True)
        response = client.post(f'/admin-users/delete/{staff2.pk}/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(pk=staff2.pk).exists())


class DuplicateEmailTest(TestCase):
    def setUp(self):
        self.existing = User.objects.create_user(
            username='owner', password='pass', email='duplicate@example.com'
        )

    def test_register_with_duplicate_email_rejected(self):
        response = self.client.post('/register/', {
            'username': 'newuser',
            'email': 'Duplicate@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'avatar': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'อีเมลนี้ถูกใช้งานแล้ว')
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_register_with_new_email_success(self):
        response = self.client.post('/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'avatar': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser', email='new@example.com').exists())

    def test_profile_update_rejects_duplicate_email(self):
        other = User.objects.create_user(username='person', password='pass')
        self.client.force_login(other)
        response = self.client.post('/profile/', {
            'username': 'person',
            'email': 'duplicate@example.com',
            'avatar': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'อีเมลนี้ถูกใช้งานแล้ว')

    def test_profile_update_keeps_own_email(self):
        self.client.force_login(self.existing)
        response = self.client.post('/profile/', {
            'username': 'owner',
            'email': 'duplicate@example.com',
            'avatar': '',
        })
        self.assertEqual(response.status_code, 302)


class QrPaymentFlowTest(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='admin2', password='pass', is_staff=True)
        self.customer = User.objects.create_user(username='cust', password='pass')
        self.sneaker = Sneaker.objects.create(
            name='Shoe', brand='Nike', size=10, price=1000, release_date='2024-01-01'
        )
        Stock.objects.create(sneaker=self.sneaker, quantity=10, location='A')
        PaymentSetting.objects.create(promptpay_id='0812345678', bank_qr_enabled=True)
        self.client = Client()
        self.client.force_login(self.customer)

    def _checkout(self, method):
        CartItem.objects.create(user=self.customer, sneaker=self.sneaker, quantity=1)
        return self.client.post('/checkout/', {
            'first_name': 'A', 'last_name': 'B', 'address': 'x',
            'postal_code': '10110', 'phone': '0812345678', 'payment_method': method,
        })

    def test_checkout_page_renders_payment_methods(self):
        CartItem.objects.create(user=self.customer, sneaker=self.sneaker, quantity=1)
        resp = self.client.get('/checkout/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'พร้อมเพย์ QR')
        self.assertContains(resp, 'เก็บเงินปลายทาง')

    def test_checkout_cod_redirects_to_success(self):
        resp = self._checkout('cod')
        order = Order.objects.latest('id')
        self.assertRedirects(resp, f'/order/success/{order.id}/')

    def test_checkout_promptpay_redirects_to_payment(self):
        resp = self._checkout('promptpay')
        order = Order.objects.latest('id')
        self.assertRedirects(resp, f'/order/payment/{order.id}/')
        self.assertEqual(order.payment_method, 'promptpay')
        self.assertEqual(order.payment_status, 'unpaid')

    def test_payment_page_shows_promptpay_payload(self):
        self._checkout('promptpay')
        order = Order.objects.latest('id')
        resp = self.client.get(f'/order/payment/{order.id}/')
        self.assertEqual(resp.status_code, 200)
        payload = generate_promptpay_payload('0812345678', order.total_price())
        self.assertContains(resp, payload)

    def test_submit_payment_without_slip_fails(self):
        self._checkout('promptpay')
        order = Order.objects.latest('id')
        resp = self.client.post(f'/order/payment/{order.id}/submit/', {})
        self.assertRedirects(resp, f'/order/payment/{order.id}/')
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'unpaid')

    def test_submit_payment_with_slip(self):
        self._checkout('promptpay')
        order = Order.objects.latest('id')
        slip = SimpleUploadedFile('slip.png', PNG_BYTES, content_type='image/png')
        resp = self.client.post(
            f'/order/payment/{order.id}/submit/',
            {'payment_slip': slip, 'payment_reference': 'ref123'},
        )
        self.assertRedirects(resp, f'/order/success/{order.id}/')
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'submitted')
        self.assertEqual(order.payment_reference, 'ref123')

    def test_cod_payment_page_redirects_to_success(self):
        self._checkout('cod')
        order = Order.objects.latest('id')
        resp = self.client.get(f'/order/payment/{order.id}/')
        self.assertRedirects(resp, f'/order/success/{order.id}/')

    def test_admin_confirm_payment(self):
        self._checkout('promptpay')
        order = Order.objects.latest('id')
        admin = Client()
        admin.force_login(self.staff)
        resp = admin.post(f'/admin-orders/payment/confirm/{order.pk}/', {'payment_note': 'ok'})
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'paid')
        self.assertEqual(order.status, 'Shipping')
        self.assertIsNotNone(order.paid_at)

    def test_admin_reject_payment(self):
        self._checkout('promptpay')
        order = Order.objects.latest('id')
        admin = Client()
        admin.force_login(self.staff)
        admin.post(f'/admin-orders/payment/reject/{order.pk}/', {'payment_note': 'bad slip'})
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'rejected')
        self.assertEqual(order.payment_note, 'bad slip')

    def test_promptpay_payload_helper(self):
        payload = generate_promptpay_payload('0812345678', 100)
        self.assertTrue(payload.startswith('000201010212'))
        self.assertTrue(payload.endswith('6304F142'))
        self.assertEqual(generate_promptpay_payload('bad', 100), '')
