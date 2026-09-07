from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from functools import wraps

from .models import Sneaker, Stock, Employee, CartItem, Profile, Order, OrderItem
from .forms import SneakerForm, StockForm, EmployeeForm, RegisterForm, CheckoutForm


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
    context = {
        'total_sneakers': total_sneakers,
        'total_stock': total_stock,
        'total_employees': total_employees,
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
    stocks = Stock.objects.all().order_by('-last_updated')
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
    employees = Employee.objects.all().order_by('-id')
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
    return render(request, 'sneaker_app/cart_list.html', {'items': items, 'total': total})


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


@login_required(login_url='/login/')
def add_to_cart(request, pk):
    sneaker = get_object_or_404(Sneaker, pk=pk)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, sneaker=sneaker)
    if not created:
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

    total = sum(item.total_price() for item in items)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
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
            messages.success(request, f"สั่งซื้อสำเร็จ! หมายเลขออเดอร์ #{order.id}")
            return redirect('order_success', order_id=order.id)
    else:
        form = CheckoutForm()
    return render(request, 'sneaker_app/checkout.html', {'form': form, 'items': items, 'total': total})


@login_required(login_url='/login/')
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'sneaker_app/order_success.html', {'order': order})


@login_required(login_url='/login/')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    return render(request, 'sneaker_app/my_orders.html', {'orders': orders})


@admin_required
def admin_orders(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')
    if query:
        orders = orders.filter(Q(user__username__icontains=query) | Q(id__icontains=query) | Q(phone__icontains=query))
    if status:
        orders = orders.filter(status=status)
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
