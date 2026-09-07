from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Stock, Employee, Order, Sneaker


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
        for url in ['/', '/stock/', '/employees/', '/admin-orders/', '/my-orders/', '/sneakers/']:
            response = client.get(url)
            self.assertEqual(response.status_code, 200, url)
