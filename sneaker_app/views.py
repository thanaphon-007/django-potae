from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from functools import wraps

from .models import Sneaker, Stock, Employee, CartItem, Profile, Order, OrderItem, StoreLocation, PaymentSetting
from .forms import SneakerForm, StockForm, EmployeeForm, RegisterForm, CheckoutForm, UserProfileForm
from .promptpay import generate_promptpay_payload, generate_qr_data_uri, validate_target


def admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url='/login/')
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "คุณไม่มีสิทธิ์เข้าถึงหน้านี้ (ต้องเป็นแอดมินเท่านั้น)")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


# === หน้าหลัก (Home) ===
def home(request):
    total_sneakers = Sneaker.objects.count()
    total_stock = Stock.objects.count()
    total_employees = Employee.objects.count()
    hero_sneaker = Sneaker.objects.exclude(image='').exclude(image=None).order_by('-created_at').first()
    context = {
        'total_sneakers': total_sneakers,
        'total_stock': total_stock,
        'total_employees': total_employees,
        'hero_sneaker': hero_sneaker,
    }
    if request.user.is_authenticated:
        if request.user.is_staff:
            context['total_orders'] = Order.objects.count()
        else:
            context['my_orders_count'] = Order.objects.filter(user=request.user).count()
    return render(request, 'sneaker_app/home.html', context)


# === ระบบจัดการรองเท้า ===
@login_required(login_url='/login/')
def sneaker_list(request):
    query = request.GET.get('q', '')
    if query:
        sneakers_list = Sneaker.objects.filter(Q(name__icontains=query) | Q(brand__icontains=query)).order_by('-created_at')
    else:
        sneakers_list = Sneaker.objects.all().order_by('-created_at')

    paginator = Paginator(sneakers_list, 5)
    sneakers = paginator.get_page(request.GET.get('page'))
    return render(request, 'sneaker_app/sneaker_list.html', {'sneakers': sneakers, 'query': query})


@admin_required
def sneaker_create(request):
    if request.method == 'POST':
        form = SneakerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('sneaker_list')
    else:
        form = SneakerForm()
    return render(request, 'sneaker_app/form_template.html', {'form': form, 'action': 'เพิ่มรองเท้า', 'cancel_url': 'sneaker_list'})


@admin_required
def sneaker_update(request, pk):
    sneaker = get_object_or_404(Sneaker, pk=pk)
    if request.method == 'POST':
        form = SneakerForm(request.POST, request.FILES, instance=sneaker)
        if form.is_valid():
            form.save()
            return redirect('sneaker_list')
    else:
        form = SneakerForm(instance=sneaker)
    return render(request, 'sneaker_app/form_template.html', {'form': form, 'action': 'แก้ไขรองเท้า', 'cancel_url': 'sneaker_list'})


@admin_required
def sneaker_delete(request, pk):
    sneaker = get_object_or_404(Sneaker, pk=pk)
    if request.method == 'POST':
        sneaker.delete()
        return redirect('sneaker_list')
    return render(request, 'sneaker_app/confirm_delete.html', {'item_name': sneaker.name, 'cancel_url': 'sneaker_list'})


# === ระบบจัดการคลังสินค้า (สต็อก) ===
@login_required(login_url='/login/')
def stock_list(request):
    stocks_list = Stock.objects.all().order_by('-last_updated')
    paginator = Paginator(stocks_list, 5)
    stocks = paginator.get_page(request.GET.get('page'))
    return render(request, 'sneaker_app/stock_list.html', {'stocks': stocks})


@admin_required
def stock_create(request):
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('stock_list')
    else:
        form = StockForm()
    return render(request, 'sneaker_app/form_template.html', {'form': form, 'action': 'เพิ่มคลังสินค้า', 'cancel_url': 'stock_list'})


@admin_required
def stock_update(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            return redirect('stock_list')
    else:
        form = StockForm(instance=stock)
    return render(request, 'sneaker_app/form_template.html', {'form': form, 'action': 'แก้ไขคลังสินค้า', 'cancel_url': 'stock_list'})


@admin_required
def stock_delete(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        stock.delete()
        return redirect('stock_list')
    return render(request, 'sneaker_app/confirm_delete.html', {'item_name': stock.sneaker.name, 'cancel_url': 'stock_list'})


# === ระบบจัดการพนักงาน ===
@login_required(login_url='/login/')
def employee_list(request):
    employees_list = Employee.objects.all().order_by('-id')
    paginator = Paginator(employees_list, 5)
    employees = paginator.get_page(request.GET.get('page'))
    return render(request, 'sneaker_app/employee_list.html', {'employees': employees})


@admin_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'sneaker_app/form_template.html', {'form': form, 'action': 'เพิ่มข้อมูลพนักงาน', 'cancel_url': 'employee_list'})


@admin_required
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'sneaker_app/form_template.html', {'form': form, 'action': 'แก้ไขข้อมูลพนักงาน', 'cancel_url': 'employee_list'})


@admin_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        return redirect('employee_list')
    return render(request, 'sneaker_app/confirm_delete.html', {'item_name': f"{employee.first_name} {employee.last_name}", 'cancel_url': 'employee_list'})


# === ตะกร้าสินค้า ===
@login_required(login_url='/login/')
def cart_list(request):
    items = CartItem.objects.filter(user=request.user).select_related('sneaker')
    total = sum(item.total_price() for item in items)
    has_out_of_stock = any(not item.sneaker.is_in_stock() or item.quantity > item.sneaker.available_stock() for item in items)
    return render(request, 'sneaker_app/cart_list.html', {'items': items, 'total': total, 'has_out_of_stock': has_out_of_stock})


@admin_required
def admin_carts(request):
    query = request.GET.get('q', '').strip()
    items = CartItem.objects.select_related('user', 'sneaker').order_by('user__username', '-added_at')
    if query:
        items = items.filter(user__username__icontains=query)
    grouped = {}
    for item in items:
        key = item.user_id
        if key not in grouped:
            grouped[key] = {'user': item.user, 'items': [], 'total': 0}
        grouped[key]['items'].append(item)
        grouped[key]['total'] += item.total_price()
    carts = list(grouped.values())
    return render(request, 'sneaker_app/admin_carts.html', {'carts': carts, 'query': query})


@admin_required
def admin_remove_cart_item(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk)
    if request.method == 'POST':
        username = cart_item.user.username
        item_name = cart_item.sneaker.name
        cart_item.delete()
        messages.success(request, f"ลบ {item_name} ออกจากตะกร้าของ {username} แล้ว")
    return redirect('admin_carts')


@admin_required
def admin_clear_cart(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        count = CartItem.objects.filter(user=user).count()
        CartItem.objects.filter(user=user).delete()
        if count:
            messages.success(request, f"ล้างตะกร้าของ {user.username} แล้ว ({count} รายการ)")
        else:
            messages.info(request, f"ตะกร้าของ {user.username} ว่างอยู่แล้ว")
    return redirect('admin_carts')


@login_required(login_url='/login/')
def add_to_cart(request, pk):
    sneaker = get_object_or_404(Sneaker, pk=pk)
    if not sneaker.is_in_stock():
        messages.error(request, f"{sneaker.name} สินค้าหมด ไม่สามารถสั่งซื้อได้ในขณะนี้")
        return redirect('sneaker_list')
    cart_item, created = CartItem.objects.get_or_create(user=request.user, sneaker=sneaker)
    if not created:
        available = sneaker.available_stock()
        if cart_item.quantity + 1 > available:
            messages.error(request, f"จำนวนเกินสต็อกคงเหลือ ({available} คู่)")
            return redirect('cart_list')
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"เพิ่ม {sneaker.name} ลงตะกร้าแล้ว")
    return redirect('cart_list')


@login_required(login_url='/login/')
def update_cart_quantity(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, user=request.user)
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                cart_item.delete()
                messages.success(request, "ลบสินค้าออกจากตะกร้าแล้ว")
            else:
                available = cart_item.sneaker.available_stock()
                if quantity > available:
                    messages.error(request, f"จำนวนเกินสต็อกคงเหลือ ({available} คู่) กรุณาลดจำนวนลง")
                    return redirect('cart_list')
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "อัปเดตจำนวนสินค้าแล้ว")
        except ValueError:
            messages.error(request, "จำนวนสินค้าไม่ถูกต้อง")
    return redirect('cart_list')


@login_required(login_url='/login/')
def remove_from_cart(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, user=request.user)
    cart_item.delete()
    messages.success(request, "ลบสินค้าออกจากตะกร้าแล้ว")
    return redirect('cart_list')


# === ระบบสั่งซื้อ (Checkout) ===
@login_required(login_url='/login/')
def checkout(request):
    items = CartItem.objects.filter(user=request.user).select_related('sneaker')
    if not items:
        messages.warning(request, "ตะกร้าของคุณว่างเปล่า กรุณาเลือกสินค้าก่อน")
        return redirect('cart_list')

    for item in items:
        available = item.sneaker.available_stock()
        if available <= 0:
            messages.error(request, f"{item.sneaker.name} สินค้าหมด ไม่สามารถสั่งซื้อได้ กรุณานำออกจากตะกร้า")
            return redirect('cart_list')
        if item.quantity > available:
            messages.error(request, f"{item.sneaker.name} เหลือสต็อกเพียง {available} คู่ กรุณาปรับจำนวนในตะกร้า")
            return redirect('cart_list')

    total = sum(item.total_price() for item in items)
    setting = PaymentSetting.get_solo()
    enabled_methods = setting.enabled_methods()

    if request.method == 'POST':
        form = CheckoutForm(request.POST, enabled_methods=enabled_methods)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    sneaker=item.sneaker,
                    quantity=item.quantity,
                    price=item.sneaker.price,
                )
            items.delete()
            if order.is_qr_payment():
                messages.success(request, f"สั่งซื้อสำเร็จ! หมายเลขออเดอร์ #{order.id} กรุณาชำระเงิน")
                return redirect('payment_page', order_id=order.id)
            messages.success(request, f"สั่งซื้อสำเร็จ! หมายเลขออเดอร์ #{order.id}")
            return redirect('order_success', order_id=order.id)
    else:
        form = CheckoutForm(enabled_methods=enabled_methods)
    return render(request, 'sneaker_app/checkout.html', {
        'form': form,
        'items': items,
        'total': total,
        'setting': setting,
    })


@login_required(login_url='/login/')
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'sneaker_app/order_success.html', {'order': order})


# === ระบบชำระเงินผ่าน QR Code ===
@login_required(login_url='/login/')
def payment_page(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if order.payment_method == 'cod':
        messages.info(request, "ออเดอร์นี้เลือกเก็บเงินปลายทาง ไม่ต้องชำระเงินล่วงหน้า")
        return redirect('order_success', order_id=order.id)
    if order.payment_status == 'paid':
        messages.info(request, "ออเดอร์นี้ชำระเงินเรียบร้อยแล้ว")
        return redirect('order_success', order_id=order.id)

    setting = PaymentSetting.get_solo()
    promptpay_qr = ''
    promptpay_error = ''
    if order.payment_method == 'promptpay':
        promptpay_error = validate_target(setting.promptpay_id)
        if not promptpay_error:
            payload = generate_promptpay_payload(setting.promptpay_id, order.total_price())
            promptpay_qr = generate_qr_data_uri(payload)
            if not promptpay_qr:
                promptpay_error = 'ไม่สามารถสร้างคิวอาร์โค้ดได้ กรุณาติดต่อร้านค้า'

    return render(request, 'sneaker_app/payment.html', {
        'order': order,
        'setting': setting,
        'promptpay_qr': promptpay_qr,
        'promptpay_error': promptpay_error,
    })


@login_required(login_url='/login/')
def submit_payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if request.method != 'POST':
        return redirect('payment_page', order_id=order.id)
    if order.payment_method == 'cod' or order.payment_status == 'paid':
        return redirect('order_success', order_id=order.id)

    slip = request.FILES.get('payment_slip')
    reference = request.POST.get('payment_reference', '').strip()
    if slip:
        order.payment_slip = slip
    if reference:
        order.payment_reference = reference

    if not order.payment_slip:
        messages.error(request, "กรุณาแนบสลิปการโอนเงินก่อนแจ้งชำระ")
        return redirect('payment_page', order_id=order.id)

    order.payment_status = 'submitted'
    order.payment_note = ''
    order.save()
    messages.success(request, "แจ้งชำระเงินเรียบร้อยแล้ว รอแอดมินตรวจสอบสลิป")
    return redirect('order_success', order_id=order.id)


# === ตรวจสอบการชำระเงิน (Admin) ===
@admin_required
def admin_confirm_payment(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.payment_status = 'paid'
        order.paid_at = timezone.now()
        order.payment_note = request.POST.get('payment_note', '').strip()
        if order.status == 'Pending':
            order.status = 'Shipping'
        order.save()
        messages.success(request, f"ยืนยันการชำระเงินออเดอร์ #{order.id} แล้ว")
    return redirect('admin_orders')


@admin_required
def admin_reject_payment(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.payment_status = 'rejected'
        order.payment_note = request.POST.get('payment_note', '').strip()
        order.save()
        messages.warning(request, f"ปฏิเสธการชำระเงินออเดอร์ #{order.id} แล้ว")
    return redirect('admin_orders')


@login_required(login_url='/login/')
def my_orders(request):
    orders_list = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    paginator = Paginator(orders_list, 5)
    orders = paginator.get_page(request.GET.get('page'))
    return render(request, 'sneaker_app/my_orders.html', {'orders': orders})


@admin_required
def admin_orders(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    orders_list = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')
    if query:
        orders_list = orders_list.filter(Q(user__username__icontains=query) | Q(id__icontains=query) | Q(phone__icontains=query))
    if status:
        orders_list = orders_list.filter(status=status)
    paginator = Paginator(orders_list, 5)
    orders = paginator.get_page(request.GET.get('page'))
    return render(request, 'sneaker_app/admin_orders.html', {'orders': orders, 'query': query, 'status': status})


@admin_required
def update_order_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"อัปเดตสถานะออเดอร์ #{order.id} เป็น {order.get_status_display()} แล้ว")
        else:
            messages.error(request, "สถานะไม่ถูกต้อง")
    return redirect('admin_orders')


@login_required(login_url='/login/')
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method == 'POST':
        order.delete()
        messages.success(request, f"ลบออเดอร์ #{order.id} สำเร็จแล้ว")
        return redirect('my_orders')
    return render(request, 'sneaker_app/confirm_delete.html', {'item_name': f"ออเดอร์ #{order.id}", 'cancel_url': 'my_orders'})


@admin_required
def admin_order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        messages.success(request, f"ลบออเดอร์ #{order.id} สำเร็จแล้ว")
        return redirect('admin_orders')
    return render(request, 'sneaker_app/confirm_delete.html', {'item_name': f"ออเดอร์ #{order.id} ของ {order.user.username}", 'cancel_url': 'admin_orders'})


# === จัดการสิทธิ์ผู้ใช้ (Admin) ===
@admin_required
def admin_users(request):
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()
    users_list = User.objects.all().order_by('-date_joined')
    if query:
        users_list = users_list.filter(Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query))
    if role == 'admin':
        users_list = users_list.filter(is_staff=True)
    elif role == 'member':
        users_list = users_list.filter(is_staff=False)
    paginator = Paginator(users_list, 5)
    users = paginator.get_page(request.GET.get('page'))
    return render(request, 'sneaker_app/admin_users.html', {'users': users, 'query': query, 'role': role})


@admin_required
def update_user_role(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role not in ['admin', 'member']:
            messages.error(request, "สิทธิ์ไม่ถูกต้อง")
            return redirect('admin_users')
        if target.pk == request.user.pk:
            messages.error(request, "ไม่สามารถเปลี่ยนสิทธิ์ของตัวเองผ่านหน้านี้ได้ (ห้ามถอดสิทธิ์ตัวเอง)")
            return redirect('admin_users')
        if new_role == 'admin':
            target.is_staff = True
            target.save()
            messages.success(request, f"เลื่อนสิทธิ์ {target.username} เป็นแอดมินแล้ว")
        else:
            target.is_staff = False
            target.save()
            messages.success(request, f"ปรับสิทธิ์ {target.username} เป็นสมาชิกแล้ว")
    return redirect('admin_users')


@admin_required
def toggle_user_active(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        if target.pk == request.user.pk:
            messages.error(request, "ไม่สามารถปิดใช้งานบัญชีของตัวเองได้")
            return redirect('admin_users')
        target.is_active = not target.is_active
        target.save()
        if target.is_active:
            messages.success(request, f"เปิดใช้งานบัญชี {target.username} แล้ว")
        else:
            messages.success(request, f"ปิดใช้งานบัญชี {target.username} แล้ว")
    return redirect('admin_users')


@admin_required
def delete_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target.pk == request.user.pk:
        messages.error(request, "ไม่สามารถลบบัญชีของตัวเองได้")
        return redirect('admin_users')
    if request.method == 'POST':
        username = target.username
        target.delete()
        messages.success(request, f"ลบบัญชี @{username} และข้อมูลทั้งหมด (คำสั่งซื้อ/ตะกร้า/โปรไฟล์) แล้ว")
        return redirect('admin_users')
    return render(request, 'sneaker_app/confirm_delete.html', {'item_name': f"บัญชีผู้ใช้ @{target.username}", 'cancel_url': 'admin_users'})


# === ระบบสมาชิก (Authentication) ===
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.is_staff = False
            user.save()
            Profile.objects.create(user=user, avatar=form.cleaned_data.get('avatar'))
            login(request, user)
            messages.success(request, "สมัครสมาชิกสำเร็จ ยินดีต้อนรับ!")
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'sneaker_app/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
        else:
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    else:
        form = AuthenticationForm()
    return render(request, 'sneaker_app/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# === โปรไฟล์ผู้ใช้ ===
@login_required(login_url='/login/')
def profile_view(request):
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            avatar = form.cleaned_data.get('avatar')
            if avatar:
                profile.avatar = avatar
                profile.save()
            messages.success(request, "อัปเดตโปรไฟล์เรียบร้อยแล้ว")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)

    orders_count = Order.objects.filter(user=request.user).count()
    return render(request, 'sneaker_app/profile.html', {
        'form': form,
        'profile': profile,
        'orders_count': orders_count,
    })


# === แผนที่สาขาร้านค้า (Google Maps) ===
def store_map(request):
    from django.conf import settings
    stores = StoreLocation.objects.filter(is_active=True).order_by('-id')
    default_lat = float(stores[0].latitude) if stores else 13.7563
    default_lng = float(stores[0].longitude) if stores else 100.5018
    default_map_url = (
        f'https://maps.google.com/maps?q={default_lat},{default_lng}&z=16&output=embed'
    )
    return render(request, 'sneaker_app/store_map.html', {
        'api_key': settings.GOOGLE_MAPS_API_KEY,
        'stores': [store.to_dict() for store in stores],
        'default_map_url': default_map_url,
    })

## === API JSON สำหรับสาขาร้านค้า ===
def store_api(request):
    """API JSON: รายชื่อสาขาร้านค้า พร้อมพิกัด lat/lng สำหรับแสดงบน Google Maps"""
    stores = StoreLocation.objects.filter(is_active=True).order_by('name')
    data = {
        'status': 'success',
        'count': stores.count(),
        'stores': [store.to_dict() for store in stores],
    }
    return JsonResponse(data)
