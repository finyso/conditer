from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from datetime import date, timedelta

class Employee(models.Model):
    """Сотрудники (18+)"""
    POSITION_CHOICES = [
        ('confectioner', 'Кондитер'),
        ('manager', 'Менеджер'),
        ('courier', 'Курьер'),
        ('admin_shop', 'Администратор'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$')]
    )
    email = models.EmailField()
    date_of_birth = models.DateField()
    hire_date = models.DateField(auto_now_add=True)
    photo = models.ImageField(upload_to='employees/', null=True, blank=True)
    description = models.TextField(blank=True)
    
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def save(self, *args, **kwargs):
        if self.age() < 18:
            raise ValueError("Сотрудник должен быть старше 18 лет")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.get_position_display()}"

class Category(models.Model):
    """Виды изделий"""
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    """Изделия"""
    UNIT_CHOICES = [
        ('pcs', 'штуки'),
        ('kg', 'килограммы'),
        ('g', 'граммы'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    unit = models.CharField(max_length=3, choices=UNIT_CHOICES, default='pcs')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField()
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    ingredients = models.ManyToManyField('Ingredient', through='ProductIngredient')
    
    def __str__(self):
        return f"{self.name} - {self.price} руб."

class Ingredient(models.Model):
    """Ингредиенты"""
    name = models.CharField(max_length=50)
    unit = models.CharField(max_length=20)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name

class ProductIngredient(models.Model):
    """Связь продукт-ингредиент"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

class Client(models.Model):
    """Клиенты (18+)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$')]
    )
    email = models.EmailField()
    address = models.TextField()
    date_of_birth = models.DateField()
    registered_at = models.DateTimeField(auto_now_add=True)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def save(self, *args, **kwargs):
        if self.age() < 18:
            raise ValueError("Клиент должен быть старше 18 лет")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.phone})"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('confirmed', 'Подтвержден'),
        ('preparing', 'Готовится'),
        ('delivering', 'Доставляется'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменен'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='orders')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promo_code = models.ForeignKey('PromoCode', on_delete=models.SET_NULL, null=True, blank=True)
    pickup_point = models.ForeignKey('PickupPoint', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Заказ #{self.id} - {self.client.name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2)
    
    def subtotal(self):
        qty = self.quantity if self.quantity is not None else 0
        price = self.price_at_time if self.price_at_time is not None else 0
        return qty * price
    
    def save(self, *args, **kwargs):
        if not self.price_at_time and self.product:
            self.price_at_time = self.product.price
        super().save(*args, **kwargs)

class PromoCode(models.Model):
    """Промокоды и купоны"""
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    max_uses = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    
    @property
    def is_valid(self):
        now = timezone.now()
        return (self.is_active and 
                self.valid_from <= now <= self.valid_to and
                self.used_count < self.max_uses)
    
    def __str__(self):
        return f"{self.code} ({self.discount_percent}%)"

class Review(models.Model):
    """Отзывы"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Отзыв от {self.client.name} - {self.rating}★"

class News(models.Model):
    """Новости"""
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=300)
    content = models.TextField()
    image = models.ImageField(upload_to='news/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class GlossaryTerm(models.Model):
    """Словарь терминов"""
    term = models.CharField(max_length=100)
    definition = models.TextField()
    added_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.term

class Vacancy(models.Model):
    """Вакансии"""
    title = models.CharField(max_length=100)
    description = models.TextField()
    requirements = models.TextField()
    salary = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class Contact(models.Model):
    """Контакты сотрудников"""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    work_phone = models.CharField(max_length=20)
    work_email = models.EmailField()
    responsibilities = models.TextField()
    
    def __str__(self):
        return f"Контакты {self.employee.name}"
    
class PickupPoint(models.Model):
    """Точки самовывоза"""
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    work_hours = models.CharField(max_length=100, default='09:00-21:00')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class CompanyInfo(models.Model):
    """Информация о компании"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.key