from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Client, Review, Order, PromoCode, PickupPoint, OrderItem, Product
from datetime import date
import re

class ClientRegistrationForm(UserCreationForm):
    name = forms.CharField(max_length=100, label='ФИО')
    phone = forms.CharField(max_length=20, label='Телефон')
    address = forms.CharField(widget=forms.Textarea, label='Адрес')
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Дата рождения'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        pattern = r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$'
        if not re.match(pattern, phone):
            raise ValidationError('Телефон должен быть в формате +375 (29) XXX-XX-XX')
        return phone
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise ValidationError('Вы должны быть старше 18 лет для регистрации')
        return dob
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            Client.objects.create(
                user=user,
                name=self.cleaned_data['name'],
                phone=self.cleaned_data['phone'],
                email=user.email,
                address=self.cleaned_data['address'],
                date_of_birth=self.cleaned_data['date_of_birth']
            )
        return user

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['product', 'rating', 'text']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} ★') for i in range(1, 6)]),
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Ваш отзыв...'}),
        }
    
    def clean_text(self):
        text = self.cleaned_data['text']
        if len(text) < 10:
            raise ValidationError('Отзыв должен содержать минимум 10 символов')
        return text

class OrderForm(forms.ModelForm):
    promo_code = forms.CharField(max_length=50, required=False, label='Промокод')
    DELIVERY_CHOICES = [
        ('delivery', 'Доставка'),
        ('pickup', 'Самовывоз'),
    ]
    delivery_method = forms.ChoiceField(
        choices=DELIVERY_CHOICES,
        widget=forms.RadioSelect,
        initial='delivery',
        label='Способ получения'
    )
    pickup_point = forms.ModelChoiceField(
        queryset=PickupPoint.objects.filter(is_active=True),
        required=False,
        label='Точка самовывоза'
    )
    delivery_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        label='Дата доставки'
    )
    
    class Meta:
        model = Order
        fields = ['delivery_address', 'delivery_method', 'pickup_point', 'delivery_date']
        widgets = {
            'delivery_address': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Город, улица, дом, квартира'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        delivery_method = cleaned_data.get('delivery_method')
        delivery_address = cleaned_data.get('delivery_address')
        pickup_point = cleaned_data.get('pickup_point')
        
        if delivery_method == 'delivery' and not delivery_address:
            self.add_error('delivery_address', 'Укажите адрес доставки')
        if delivery_method == 'pickup' and not pickup_point:
            self.add_error('pickup_point', 'Выберите точку самовывоза')
        
        return cleaned_data
    
    def clean_promo_code(self):
        code = self.cleaned_data.get('promo_code')
        if code:
            try:
                promo = PromoCode.objects.get(code=code)
                if not promo.is_valid:
                    raise ValidationError('Промокод недействителен')
                return promo
            except PromoCode.DoesNotExist:
                raise ValidationError('Промокод не найден')
        return None

class OrderItemForm(forms.ModelForm):
    """Форма для добавления/редактирования товара в заказе"""
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price_at_time']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'price_at_time': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_available=True)
        self.fields['product'].label = 'Товар'
        self.fields['quantity'].label = 'Количество'
        self.fields['price_at_time'].label = 'Цена за единицу'
    
    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        if quantity and quantity < 1:
            self.add_error('quantity', 'Количество должно быть больше 0')
        return cleaned_data