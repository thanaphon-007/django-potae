from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Sneaker, Stock, Employee, Profile, Order, PaymentSetting
from .promptpay import validate_target

class SneakerForm(forms.ModelForm):
    class Meta:
        model = Sneaker
        fields = ['name', 'brand', 'description', 'size', 'price', 'release_date', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'size': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'release_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['sneaker', 'quantity', 'location', 'status']
        widgets = {
            'sneaker': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['photo', 'first_name', 'last_name', 'nickname', 'position', 'phone', 'salary']
        widgets = {
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อจริง'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'นามสกุล'}),
            'nickname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อเล่น'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08x-xxx-xxxx'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'ระบุเงินเดือน'}),
        }

class RegisterForm(UserCreationForm):
    avatar = forms.ImageField(
        required=False,
        label="รูปโปรไฟล์",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        label="อีเมล",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'})
    )

    class Meta(UserCreationForm.Meta):
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'ชื่อผู้ใช้'})
        for name in ['password1', 'password2']:
            self.fields[name].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("อีเมลนี้ถูกใช้งานแล้ว กรุณาใช้อีเมลอื่น")
        return email

class UserProfileForm(forms.ModelForm):
    avatar = forms.ImageField(
        required=False,
        label="รูปโปรไฟล์",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อ'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'นามสกุล'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'}),
        }
        labels = {
            'username': 'ชื่อผู้ใช้',
            'first_name': 'ชื่อ',
            'last_name': 'นามสกุล',
            'email': 'อีเมล',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("อีเมลนี้ถูกใช้งานแล้ว กรุณาใช้อีเมลอื่น")
        return email


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'address', 'postal_code', 'phone', 'payment_method']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อ'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'นามสกุล'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'เช่น ถนนสุขุมวิท เขตคลองเตย กรุงเทพฯ'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น 10110', 'maxlength': '5', 'pattern': '[0-9]{5}', 'title': 'ระบุรหัสไปรษณีย์ 5 หลัก'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08x-xxx-xxxx'}),
            'payment_method': forms.RadioSelect(),
        }
        labels = {
            'first_name': 'ชื่อ',
            'last_name': 'นามสกุล',
            'address': 'ที่อยู่จัดส่ง',
            'postal_code': 'รหัสไปรษณีย์',
            'phone': 'เบอร์โทรศัพท์',
            'payment_method': 'วิธีชำระเงิน',
        }

    def __init__(self, *args, enabled_methods=None, **kwargs):
        super().__init__(*args, **kwargs)
        if enabled_methods:
            self.fields['payment_method'].choices = [
                (value, label) for value, label in Order.PAYMENT_METHOD_CHOICES
                if value in enabled_methods
            ]
            self.fields['payment_method'].initial = enabled_methods[0]

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code', '').strip()
        if not postal_code.isdigit() or len(postal_code) != 5:
            raise forms.ValidationError("รหัสไปรษณีย์ต้องเป็นตัวเลข 5 หลักเท่านั้น")
        return postal_code


class PaymentSettingForm(forms.ModelForm):
    class Meta:
        model = PaymentSetting
        fields = '__all__'

    def clean_promptpay_id(self):
        value = self.cleaned_data.get('promptpay_id', '').strip()
        if value:
            error = validate_target(value)
            if error:
                raise forms.ValidationError(error)
        return value