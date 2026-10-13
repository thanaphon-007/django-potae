from django.db import models
from django.contrib.auth.models import User

# ระบบหลัก 1: จัดการรองเท้า
class Sneaker(models.Model):
    BRAND_CHOICES = [
        ('Nike', 'Nike'),
        ('Adidas', 'Adidas'),
        ('New Balance', 'New Balance'),
        ('Asics', 'Asics'),
        ('Vans', 'Vans'),
        ('Other', 'Other'),
    ]
    name = models.CharField(max_length=200, verbose_name='ชื่อรุ่นรองเท้า')
    brand = models.CharField(max_length=50, choices=BRAND_CHOICES, verbose_name='แบรนด์')
    description = models.TextField(blank=True, verbose_name='รายละเอียด')
    size = models.DecimalField(max_digits=4, decimal_places=1, verbose_name='ไซส์ (US)')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='ราคา (บาท)')
    release_date = models.DateField(verbose_name='วันที่วางจำหน่าย')
    image = models.ImageField(upload_to='sneakers/', null=True, blank=True, verbose_name='รูปภาพ')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.name} (Size: {self.size})"

    def available_stock(self):
        total = self.stock_set.aggregate(total=models.Sum('quantity'))['total'] or 0
        return total

    def is_in_stock(self):
        return self.available_stock() > 0

# ระบบหลัก 2: จัดการคลังสินค้า (สต็อก)
class Stock(models.Model):
    STATUS_CHOICES = [
        ('In Stock', 'มีสินค้า'),
        ('Out of Stock', 'สินค้าหมด'),
        ('Pre-order', 'พรีออเดอร์'),
    ]
    sneaker = models.ForeignKey(Sneaker, on_delete=models.CASCADE, verbose_name='เลือกรองเท้า')
    quantity = models.IntegerField(default=0, verbose_name='จำนวนในคลัง (คู่)')
    location = models.CharField(max_length=100, verbose_name='สถานที่เก็บ (เช่น โกดัง A)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='In Stock', verbose_name='สถานะ')
    last_updated = models.DateTimeField(auto_now=True, verbose_name='อัปเดตล่าสุด')

    def __str__(self):
        return f"สต็อก: {self.sneaker.name} - จำนวน {self.quantity} คู่"

# ระบบหลัก 3: จัดการพนักงาน
class Employee(models.Model):
    POSITION_CHOICES = [
        ('Staff', 'พนักงานทั่วไป'),
        ('Manager', 'ผู้จัดการ'),
        ('Cashier', 'แคชเชียร์'),
        ('Stock', 'ฝ่ายสต็อกสินค้า'),
    ]
    
    first_name = models.CharField(max_length=100, verbose_name="ชื่อ")
    last_name = models.CharField(max_length=100, verbose_name="นามสกุล")
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name="ชื่อเล่น")
    position = models.CharField(max_length=50, choices=POSITION_CHOICES, default='Staff', verbose_name="ตำแหน่ง")
    phone = models.CharField(max_length=20, verbose_name="เบอร์โทรศัพท์")
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="เงินเดือน (บาท)")
    joined_date = models.DateField(auto_now_add=True, verbose_name="วันที่เริ่มงาน")
    photo = models.ImageField(upload_to='employees/', null=True, blank=True, verbose_name="รูปพนักงาน")

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.position})"


# ระบบหลัก 4: ตะกร้าสินค้า
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ผู้ใช้')
    sneaker = models.ForeignKey(Sneaker, on_delete=models.CASCADE, verbose_name='สินค้า')
    quantity = models.PositiveIntegerField(default=1, verbose_name='จำนวน')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่เพิ่ม')

    class Meta:
        unique_together = ('user', 'sneaker')

    def __str__(self):
        return f"{self.user.username} - {self.sneaker.name} x{self.quantity}"

    def total_price(self):
        return self.sneaker.price * self.quantity


# ระบบหลัก 5: โปรไฟล์สมาชิก
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='รูปโปรไฟล์')

    def __str__(self):
        return f"โปรไฟล์ของ {self.user.username}"


# ระบบหลัก 6: คำสั่งซื้อ
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'รอดำเนินการ'),
        ('Shipping', 'กำลังจัดส่ง'),
        ('Completed', 'จัดส่งแล้ว'),
        ('Cancelled', 'ยกเลิก'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='ผู้สั่งซื้อ')
    first_name = models.CharField(max_length=100, default='', verbose_name='ชื่อ')
    last_name = models.CharField(max_length=100, default='', verbose_name='นามสกุล')
    address = models.TextField(verbose_name='ที่อยู่จัดส่ง')
    postal_code = models.CharField(max_length=10, default='', verbose_name='รหัสไปรษณีย์')
    phone = models.CharField(max_length=20, verbose_name='เบอร์โทรศัพท์')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', verbose_name='สถานะ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่สั่งซื้อ')

    def __str__(self):
        return f"ออเดอร์ #{self.id} โดย {self.user.username}"

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='คำสั่งซื้อ')
    sneaker = models.ForeignKey(Sneaker, on_delete=models.CASCADE, verbose_name='สินค้า')
    quantity = models.PositiveIntegerField(default=1, verbose_name='จำนวน')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='ราคา/คู่')

    def __str__(self):
        return f"{self.sneaker.name} x{self.quantity}"

    def total_price(self):
        return self.price * self.quantity


# ระบบหลัก 7: สาขาร้านค้า (สำหรับแผนที่ Google Maps) โครงสร้างฐานข้อมูล 
class StoreLocation(models.Model):
    name = models.CharField(max_length=200, verbose_name='ชื่อสาขา')
    address = models.TextField(verbose_name='ที่อยู่')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='ละติจูด (Latitude)')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='ลองจิจูด (Longitude)')
    phone = models.CharField(max_length=20, blank=True, verbose_name='เบอร์โทรศัพท์')
    opening_hours = models.CharField(max_length=100, blank=True, verbose_name='เวลาทำการ')
    image = models.ImageField(upload_to='stores/', null=True, blank=True, verbose_name='รูปภาพ')
    is_active = models.BooleanField(default=True, verbose_name='เปิดใช้งาน')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'phone': self.phone,
            'opening_hours': self.opening_hours,
            'image_url': self.image.url if self.image else None,
            'maps_url': f'https://www.google.com/maps?q={self.latitude},{self.longitude}',
        }