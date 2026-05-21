from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, F
from datetime import datetime, timedelta
from .models import *
from .forms import ClientRegistrationForm, ReviewForm, OrderForm, OrderItemForm
from .api.services import get_random_fact, get_joke
import zoneinfo
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from calendar import monthcalendar, month_name
from datetime import date

def home(request):
    last_news = News.objects.filter(is_published=True).order_by('-created_at').first()
    random_fact = get_random_fact()
    random_joke = get_joke()
    
    user_tz_str = request.COOKIES.get('timezone', 'Europe/Minsk')
    
    try:
        user_tz = zoneinfo.ZoneInfo(user_tz_str)
    except:
        user_tz = zoneinfo.ZoneInfo('Europe/Minsk')
    
    current_time = timezone.now().astimezone(user_tz)
    utc_time = timezone.now() 
    
    context = {
        'last_news': last_news,
        'random_fact': random_fact,
        'random_joke': random_joke,
        'current_time': current_time,
        'current_date': current_time.strftime('%d/%m/%Y'),
        'user_timezone': user_tz_str,
        'utc_time': utc_time,
    }
    return render(request, 'shop/home.html', context)

def about(request):
    info_list = CompanyInfo.objects.all()
    return render(request, 'shop/about.html', {'info_list': info_list})

class NewsListView(ListView):
    model = News
    template_name = 'shop/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 5
    
    def get_queryset(self):
        return News.objects.filter(is_published=True).order_by('-created_at')

class NewsDetailView(DetailView):
    model = News
    template_name = 'shop/news_detail.html'
    context_object_name = 'news'

class GlossaryListView(ListView):
    model = GlossaryTerm
    template_name = 'shop/glossary.html'
    context_object_name = 'terms'
    ordering = ['term']

def contacts(request):
    contacts_list = Contact.objects.select_related('employee').all()
    return render(request, 'shop/contacts.html', {'contacts': contacts_list})

class VacancyListView(ListView):
    model = Vacancy
    template_name = 'shop/vacancies.html'
    context_object_name = 'vacancies'
    
    def get_queryset(self):
        return Vacancy.objects.filter(is_active=True)

class ReviewListView(ListView):
    model = Review
    template_name = 'shop/reviews.html'
    context_object_name = 'reviews'
    ordering = ['-created_at']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        avg_rating = Review.objects.aggregate(Avg('rating'))['rating__avg']
        context['avg_rating'] = round(avg_rating, 1) if avg_rating else 0
        context['form'] = ReviewForm()
        return context

@login_required
def add_review(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            if hasattr(request.user, 'client'):
                review.client = request.user.client
                review.save()
                messages.success(request, 'Спасибо за ваш отзыв!')
            else:
                messages.error(request, 'Только клиенты могут оставлять отзывы')
            return redirect('reviews')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    return redirect('reviews')

class PromoCodeListView(ListView):
    model = PromoCode
    template_name = 'shop/promocodes.html'
    context_object_name = 'promocodes'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        context['active_promocodes'] = PromoCode.objects.filter(
            is_active=True, valid_from__lte=now, valid_to__gte=now
        )
        context['expired_promocodes'] = PromoCode.objects.filter(
            Q(valid_to__lt=now) | Q(is_active=False)
        )
        return context
    
    def get_queryset(self):
        return PromoCode.objects.all()

class ProductListView(ListView):
    model = Product
    template_name = 'shop/products.html'
    context_object_name = 'products'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_available=True).select_related('category')
        
        # Поиск
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(category__name__icontains=search)
            )
        
        # Сортировка
        sort = self.request.GET.get('sort', 'name')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'name':
            queryset = queryset.order_by('name')
        elif sort == 'created_at':
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['current_sort'] = self.request.GET.get('sort', 'name')
        return context

def statistics(request):
    # Статистика по продажам
    total_sales = Order.objects.filter(status='completed').aggregate(
        total=Sum('total_amount'),
        count=Count('id'),
        avg=Avg('total_amount')
    )
    
    # Популярные товары с выручкой
    from django.db.models import F
    popular_products = OrderItem.objects.values('product__name', 'product__id').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price_at_time'))
    ).order_by('-total_quantity')[:5]
    
    # Продажи по категориям
    category_sales = Product.objects.values('category__name').annotate(
        total_sold=Sum('orderitem__quantity'),
        revenue=Sum(F('orderitem__quantity') * F('orderitem__price_at_time'))
    ).order_by('-revenue')
    
    # Добавляем проценты для категорий
    category_sales_list = list(category_sales)
    total_revenue_sum = sum(float(cat['revenue'] or 0) for cat in category_sales_list)
    for cat in category_sales_list:
        cat['revenue'] = float(cat['revenue'] or 0)
        cat['percentage'] = round((cat['revenue'] / total_revenue_sum * 100), 1) if total_revenue_sum > 0 else 0
    
    # Статистика по клиентам
    clients = Client.objects.all()
    ages = [c.age() for c in clients if c.age()]
    avg_age = sum(ages) / len(ages) if ages else 0
    ages.sort()
    median_age = ages[len(ages)//2] if ages else 0
    
    # Генерируем графики через matplotlib
    popular_chart = generate_popular_products_chart(request)
    category_chart = generate_category_sales_chart(request)
    trend_chart = generate_sales_trend_chart(request)
    
    context = {
        'total_sales': total_sales,
        'popular_products': popular_products,
        'category_sales': category_sales_list,
        'avg_client_age': round(avg_age, 1),
        'median_client_age': median_age,
        'popular_chart': popular_chart,
        'category_chart': category_chart,
        'trend_chart': trend_chart,
    }
    return render(request, 'shop/statistics.html', context)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from django.http import HttpResponse

def generate_popular_products_chart(request):
    """Генерация графика популярных товаров через matplotlib"""
    popular_products = OrderItem.objects.values('product__name').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]
    
    names = [item['product__name'] for item in popular_products]
    quantities = [float(item['total_quantity']) for item in popular_products]
    
    if not names:
        names = ['Нет данных']
        quantities = [0]
    
    # Создаем график
    plt.figure(figsize=(10, 6))
    plt.bar(names, quantities, color='#ff9800', edgecolor='#e65100', linewidth=2)
    plt.title('Популярные товары', fontsize=16, fontweight='bold')
    plt.xlabel('Товары', fontsize=12)
    plt.ylabel('Количество продаж (шт)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Сохраняем в байты
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    # Кодируем в base64 для вставки в HTML
    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic

def generate_category_sales_chart(request):
    """Генерация графика продаж по категориям"""
    category_sales = Product.objects.values('category__name').annotate(
        total_sold=Sum('orderitem__quantity')
    ).order_by('-total_sold')
    
    names = [item['category__name'] for item in category_sales if item['total_sold']]
    sales = [float(item['total_sold']) for item in category_sales if item['total_sold']]
    
    if not names:
        names = ['Нет данных']
        sales = [1]
    
    colors = ['#ff9800', '#4caf50', '#2196f3', '#9c27b0', '#f44336', '#00bcd4', '#795548']
    
    plt.figure(figsize=(10, 6))
    plt.pie(sales, labels=names, autopct='%1.1f%%', colors=colors[:len(names)], startangle=90)
    plt.title('Распределение продаж по категориям', fontsize=16, fontweight='bold')
    plt.axis('equal')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic

def generate_sales_trend_chart(request):
    """Генерация графика динамики продаж"""
    last_30_days = []
    for i in range(29, -1, -1):
        day = timezone.now() - timedelta(days=i)
        day_sales = Order.objects.filter(
            order_date__date=day.date(),
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        last_30_days.append({'date': day.strftime('%d/%m'), 'sales': float(day_sales)})
    
    dates = [item['date'] for item in last_30_days]
    sales = [item['sales'] for item in last_30_days]
    
    plt.figure(figsize=(12, 5))
    plt.plot(dates, sales, marker='o', linewidth=2, markersize=4, color='#ff9800')
    plt.fill_between(dates, sales, alpha=0.3, color='#ff9800')
    plt.title('Динамика продаж (последние 30 дней)', fontsize=16, fontweight='bold')
    plt.xlabel('Дата', fontsize=12)
    plt.ylabel('Выручка (руб)', fontsize=12)
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    plt.close()
    
    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic

def privacy_policy(request):
    return render(request, 'shop/privacy_policy.html')

@login_required
def order_list(request):
    if hasattr(request.user, 'client'):
        orders = Order.objects.filter(client=request.user.client).order_by('-order_date')
        return render(request, 'shop/orders.html', {'orders': orders})
    else:
        messages.error(request, 'Только клиенты могут просматривать заказы')
        return redirect('home')

@login_required
def order_create(request):
    if not hasattr(request.user, 'client'):
        messages.error(request, 'Только клиенты могут оформлять заказы')
        return redirect('home')
    
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Корзина пуста')
        return redirect('products')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            employee = Employee.objects.filter(position='manager').first()
            if not employee:
                employee = Employee.objects.first()  
            
            order = Order.objects.create(
                client=request.user.client,
                employee=employee, 
                delivery_address=form.cleaned_data.get('delivery_address', ''),
                promo_code=form.cleaned_data.get('promo_code'),
                status='pending'
            )
            
            total = 0
            for product_id, quantity in cart.items():
                product = Product.objects.get(id=product_id)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price_at_time=float(product.price)
                )
                total += float(product.price) * quantity
            
            if order.promo_code:
                total = total * (100 - order.promo_code.discount_percent) / 100
                order.promo_code.used_count += 1
                order.promo_code.save()
            
            order.total_amount = total
            order.save()
            
            request.session['cart'] = {}
            messages.success(request, f'Заказ #{order.id} успешно создан на сумму {total} руб.!')
            return redirect('orders')
    else:
        form = OrderForm()
    
    cart_items = []
    cart_total = 0
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        subtotal = float(product.price) * quantity
        cart_total += subtotal
        cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
    
    context = {
        'form': form,
        'cart_items': cart_items,
        'cart_total': cart_total,
    }
    return render(request, 'shop/order_create.html', context)

@login_required
def cart_view(request):
    """Просмотр корзины"""
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = 0
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            subtotal = float(product.price) * int(quantity)
            cart_total += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
        except Product.DoesNotExist:
            continue
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
    }
    return render(request, 'shop/cart.html', context)

@login_required
def remove_from_cart(request, product_id):
    """Удаление товара из корзины"""
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
        messages.success(request, 'Товар удален из корзины')
    return redirect('cart_view')

@login_required
def update_cart(request, product_id):
    """Обновление количества товара"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        cart = request.session.get('cart', {})
        if quantity > 0:
            cart[str(product_id)] = quantity
        elif str(product_id) in cart:
            del cart[str(product_id)]
        request.session['cart'] = cart
        messages.success(request, 'Корзина обновлена')
    return redirect('cart_view')

@login_required
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    messages.success(request, 'Товар добавлен в корзину')
    return redirect('products')

class ClientRegistrationView(CreateView):
    form_class = ClientRegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    return redirect('/')

def is_employee(user):
    return user.is_authenticated and hasattr(user, 'employee')

def is_client(user):
    return user.is_authenticated and hasattr(user, 'client')

@login_required
def pickup_points(request):
    points = PickupPoint.objects.filter(is_active=True)
    return render(request, 'shop/pickup_points.html', {'points': points})

@login_required
def employee_dashboard(request):
    """Панель сотрудника / админа для управления заказами"""
    
    if request.user.is_superuser:
        orders = Order.objects.all().order_by('-order_date')
        clients = Client.objects.all()
        sales_stats = orders.aggregate(
            total=Sum('total_amount'),
            count=Count('id'),
            avg=Avg('total_amount')
        )
        
        context = {
            'employee': None,
            'is_admin_view': True,
            'orders': orders[:20],
            'clients': clients,
            'sales_stats': sales_stats,
            'pending_count': orders.filter(status='pending').count(),
            'delivering_count': orders.filter(status='delivering').count(),
            'completed_count': orders.filter(status='completed').count(),
        }
        return render(request, 'shop/employee_dashboard.html', context)
    
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'У вас нет доступа к панели сотрудника')
        return redirect('home')
    
    employee = request.user.employee
    
    if employee.position == 'admin_shop':
        orders = Order.objects.all().order_by('-order_date')
        clients = Client.objects.all()
    else:
        orders = Order.objects.filter(employee=employee).order_by('-order_date')
        clients = Client.objects.filter(orders__employee=employee).distinct()
    
    sales_stats = orders.aggregate(
        total=Sum('total_amount'),
        count=Count('id'),
        avg=Avg('total_amount')
    )
    
    context = {
        'employee': employee,
        'is_admin_view': False,
        'orders': orders[:20],
        'clients': clients,
        'sales_stats': sales_stats,
        'pending_count': orders.filter(status='pending').count(),
        'delivering_count': orders.filter(status='delivering').count(),
        'completed_count': orders.filter(status='completed').count(),
    }
    return render(request, 'shop/employee_dashboard.html', context)

@login_required
def employee_order_detail(request, order_id):
    """Детали заказа для сотрудника/админа"""
    if not (request.user.is_superuser or hasattr(request.user, 'employee')):
        messages.error(request, 'У вас нет доступа')
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id)
    
    if hasattr(request.user, 'employee') and not request.user.is_superuser:
        employee = request.user.employee
        if employee.position != 'admin_shop' and order.employee != employee:
            messages.error(request, 'У вас нет доступа к этому заказу')
            return redirect('employee_dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Статус заказа #{order.id} изменен на "{order.get_status_display()}"')
            return redirect('employee_order_detail', order_id=order.id)
    
    return render(request, 'shop/employee_order_detail.html', {'order': order})

from django.shortcuts import redirect

def redirect_after_login(request):
    if request.user.is_superuser:
        return redirect('/admin/')
    elif hasattr(request.user, 'employee'):
        return redirect('/employee/dashboard/')
    elif hasattr(request.user, 'client'):
        return redirect('/products/')  
    else:
        return redirect('/')

@login_required
def employee_clients(request):
    if not hasattr(request.user, 'employee'):
        messages.error(request, 'У вас нет доступа')
        return redirect('home')
    
    employee = request.user.employee
    
    if employee.position == 'admin_shop':
        clients = Client.objects.all().annotate(
            orders_count=Count('orders'),
            total_spent_sum=Sum('orders__total_amount') 
        )
    else:
        clients = Client.objects.filter(orders__employee=employee).distinct().annotate(
            orders_count=Count('orders'),
            total_spent_sum=Sum('orders__total_amount') 
        )
    
    return render(request, 'shop/employee_clients.html', {'clients': clients})

from calendar import monthcalendar, month_name
from datetime import date, datetime
import pytz

def calendar_view(request):
    """Текстовый календарь"""
    from calendar import monthcalendar, month_name
    from datetime import date
    
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    cal = monthcalendar(year, month)
    
    user_tz_str = request.COOKIES.get('timezone', 'Europe/Minsk')
    try:
        user_tz = zoneinfo.ZoneInfo(user_tz_str)
    except:
        user_tz = zoneinfo.ZoneInfo('Europe/Minsk')
    
    current_time = timezone.now().astimezone(user_tz)
    utc_time = timezone.now()
    
    context = {
        'calendar': cal,
        'month_name': month_name[month],
        'year': year,
        'month': month,
        'prev_month': month - 1 if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': month + 1 if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
        'today': today.day,
        'current_time': current_time,
        'user_timezone': user_tz_str,
        'utc_time': utc_time,
    }
    return render(request, 'shop/calendar.html', context)

@login_required
def employee_order_create(request):
    """Создание заказа сотрудником для любого клиента"""
    if not (request.user.is_superuser or hasattr(request.user, 'employee')):
        messages.error(request, 'Доступ только для сотрудников')
        return redirect('home')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            client_id = request.POST.get('client_id')
            if client_id:
                client = get_object_or_404(Client, id=client_id)
            else:
                client = Client.objects.first()
            
            promo_code = form.cleaned_data.get('promo_code')
            
            order = Order.objects.create(
                client=client,
                employee=request.user.employee if hasattr(request.user, 'employee') else None,
                delivery_address=form.cleaned_data.get('delivery_address', ''),
                delivery_date=form.cleaned_data.get('delivery_date'),
                promo_code=promo_code,
                status='pending',
                total_amount=0
            )
            
            messages.success(request, f'Заказ #{order.id} создан. Теперь добавьте товары.')
            return redirect('employee_order_add_item', order_id=order.id)
    else:
        form = OrderForm()
    
    context = {
        'form': form,
        'clients': Client.objects.all(),
    }
    return render(request, 'shop/employee_order_create.html', context)

@login_required
def employee_order_edit(request, order_id):
    """Редактирование заказа сотрудником/админом"""
    if not (request.user.is_superuser or hasattr(request.user, 'employee')):
        messages.error(request, 'У вас нет доступа')
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id)
    
    if hasattr(request.user, 'employee') and not request.user.is_superuser:
        employee = request.user.employee
        if employee.position != 'admin_shop' and order.employee != employee:
            messages.error(request, 'У вас нет доступа к этому заказу')
            return redirect('employee_dashboard')
    
    if request.method == 'POST':
        client_id = request.POST.get('client')
        delivery_address = request.POST.get('delivery_address')
        status = request.POST.get('status')
        promo_code_id = request.POST.get('promo_code')
        pickup_point_id = request.POST.get('pickup_point')
        delivery_date = request.POST.get('delivery_date')
        
        if client_id:
            try:
                order.client = Client.objects.get(id=client_id)
            except Client.DoesNotExist:
                pass
        
        if delivery_address:
            order.delivery_address = delivery_address
        
        if status and status in dict(Order.STATUS_CHOICES):
            order.status = status
        
        if delivery_date:
            order.delivery_date = delivery_date
        
        if promo_code_id:
            try:
                order.promo_code = PromoCode.objects.get(id=promo_code_id)
            except PromoCode.DoesNotExist:
                order.promo_code = None
        else:
            order.promo_code = None
        
        if pickup_point_id:
            try:
                order.pickup_point = PickupPoint.objects.get(id=pickup_point_id)
            except PickupPoint.DoesNotExist:
                order.pickup_point = None
        else:
            order.pickup_point = None
        
        total = sum(item.subtotal() for item in order.items.all())
        if order.promo_code:
            total = total * (100 - order.promo_code.discount_percent) / 100
        order.total_amount = total
        
        order.save()
        messages.success(request, f'Заказ #{order.id} успешно обновлен')
        return redirect('employee_order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'clients': Client.objects.all(),
        'statuses': Order.STATUS_CHOICES,
        'promocodes': PromoCode.objects.filter(is_active=True),
        'pickup_points': PickupPoint.objects.filter(is_active=True),
    }
    return render(request, 'shop/employee_order_edit.html', context)

@login_required
def employee_order_delete(request, order_id):
    """Удаление заказа сотрудником/админом"""
    if not (request.user.is_superuser or hasattr(request.user, 'employee')):
        messages.error(request, 'У вас нет доступа')
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id)
    
    if hasattr(request.user, 'employee') and not request.user.is_superuser:
        employee = request.user.employee
        if employee.position != 'admin_shop' and order.employee != employee:
            messages.error(request, 'У вас нет доступа к этому заказу')
            return redirect('employee_dashboard')
    
    if request.method == 'POST':
        order_id_value = order.id
        order.delete()
        messages.success(request, f'Заказ #{order_id_value} успешно удален')
        return redirect('employee_dashboard')
    
    return render(request, 'shop/employee_order_confirm_delete.html', {'order': order})

@login_required
def employee_order_add_item(request, order_id):
    """Добавление товара в заказ"""
    if not (request.user.is_superuser or hasattr(request.user, 'employee')):
        messages.error(request, 'У вас нет доступа')
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id)
    
    if hasattr(request.user, 'employee') and not request.user.is_superuser:
        employee = request.user.employee
        if employee.position != 'admin_shop' and order.employee != employee:
            messages.error(request, 'У вас нет доступа к этому заказу')
            return redirect('employee_dashboard')
    
    if request.method == 'POST':
        form = OrderItemForm(request.POST)
        if form.is_valid():
            order_item = form.save(commit=False)
            order_item.order = order
            order_item.save()
            
            total = sum(item.subtotal() for item in order.items.all())
            
            if order.promo_code:
                total = total * (100 - order.promo_code.discount_percent) / 100
            
            order.total_amount = total
            order.save()
            
            messages.success(request, f'Товар "{order_item.product.name}" добавлен в заказ')
            return redirect('employee_order_detail', order_id=order.id)
    else:
        form = OrderItemForm()
    
    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'shop/employee_order_add_item.html', context)

@login_required
def employee_order_edit_item(request, order_id, item_id):
    """Редактирование товара в заказе"""
    if not (request.user.is_superuser or hasattr(request.user, 'employee')):
        messages.error(request, 'У вас нет доступа')
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id)
    order_item = get_object_or_404(OrderItem, id=item_id, order=order)
    
    if hasattr(request.user, 'employee') and not request.user.is_superuser:
        employee = request.user.employee
        if employee.position != 'admin_shop' and order.employee != employee:
            messages.error(request, 'У вас нет доступа к этому заказу')
            return redirect('employee_dashboard')
    
    if request.method == 'POST':
        form = OrderItemForm(request.POST, instance=order_item)
        if form.is_valid():
            form.save()
            
            total = sum(item.subtotal() for item in order.items.all())
            order.total_amount = total
            order.save()
            
            messages.success(request, f'Товар "{order_item.product.name}" обновлен')
            return redirect('employee_order_detail', order_id=order.id)
    else:
        form = OrderItemForm(instance=order_item)
    
    context = {
        'form': form,
        'order': order,
        'order_item': order_item,
    }
    return render(request, 'shop/employee_order_edit_item.html', context)

@login_required
def employee_order_delete_item(request, order_id, item_id):
    """Удаление товара из заказа"""
    # Проверка доступа
    if not (request.user.is_superuser or hasattr(request.user, 'employee')):
        messages.error(request, 'У вас нет доступа')
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id)
    order_item = get_object_or_404(OrderItem, id=item_id, order=order)
    
    if hasattr(request.user, 'employee') and not request.user.is_superuser:
        employee = request.user.employee
        if employee.position != 'admin_shop' and order.employee != employee:
            messages.error(request, 'У вас нет доступа к этому заказу')
            return redirect('employee_dashboard')
    
    if request.method == 'POST':
        product_name = order_item.product.name
        order_item.delete()
        
        total = sum(item.subtotal() for item in order.items.all())
        order.total_amount = total
        order.save()
        
        messages.success(request, f'Товар "{product_name}" удален из заказа')
        return redirect('employee_order_detail', order_id=order.id)
    
    return render(request, 'shop/employee_order_confirm_delete_item.html', {'order': order, 'order_item': order_item})

@login_required
def admin_categories(request):
    """Управление категориями"""
    if not request.user.is_superuser:
        return redirect('home')
    
    categories = Category.objects.all().annotate(product_count=Count('products'))
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        Category.objects.create(name=name, description=description)
        messages.success(request, f'Категория "{name}" создана')
        return redirect('admin_categories')
    
    context = {'categories': categories}
    return render(request, 'shop/admin_categories.html', context)

@login_required
def admin_sales(request):
    """Статистика продаж для админа"""
    if not request.user.is_superuser:
        return redirect('home')
    
    # Общая статистика
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status='completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Продажи по товарам
    product_sales = OrderItem.objects.values('product__name', 'product__category__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price_at_time'))
    ).order_by('-total_revenue')
    
    # Продажи по категориям
    category_sales = Product.objects.values('category__name').annotate(
        total_sold=Sum('orderitem__quantity'),
        revenue=Sum(F('orderitem__quantity') * F('orderitem__price_at_time'))
    ).order_by('-revenue')
    
    # Продажи по месяцам
    from django.db.models.functions import TruncMonth
    monthly_sales = Order.objects.filter(status='completed').annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('-month')
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'product_sales': product_sales,
        'category_sales': category_sales,
        'monthly_sales': monthly_sales,
    }
    return render(request, 'shop/admin_sales.html', context)

@login_required
def admin_manufacturers(request):
    """Управление производителями/ингредиентами"""
    if not request.user.is_superuser:
        return redirect('home')
    
    ingredients = Ingredient.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        unit = request.POST.get('unit')
        cost_per_unit = request.POST.get('cost_per_unit')
        Ingredient.objects.create(name=name, unit=unit, cost_per_unit=cost_per_unit)
        messages.success(request, f'Ингредиент "{name}" добавлен')
        return redirect('admin_manufacturers')
    
    context = {'ingredients': ingredients}
    return render(request, 'shop/admin_manufacturers.html', context)

@login_required
def admin_products(request):
    if not request.user.is_superuser:
        return redirect('home')
    
    products = Product.objects.all().select_related('category')
    total_value = sum(p.price for p in products)
    
    # Поиск
    search = request.GET.get('search', '')
    if search:
        products = products.filter(name__icontains=search)
    
    context = {
        'products': products,
        'total_inventory_value': total_value,
        'search': search,
    }
    return render(request, 'shop/admin_products.html', context)

@login_required
def admin_product_create(request):
    if not request.user.is_superuser:
        return redirect('home')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        description = request.POST.get('description')
        unit = request.POST.get('unit')
        is_available = request.POST.get('is_available') == 'on'
        
        category = get_object_or_404(Category, id=category_id)
        Product.objects.create(
            name=name,
            category=category,
            price=price,
            description=description,
            unit=unit,
            is_available=is_available
        )
        messages.success(request, f'Товар "{name}" создан')
        return redirect('admin_products')
    
    context = {'categories': Category.objects.all()}
    return render(request, 'shop/admin_product_form.html', context)

@login_required
def admin_product_edit(request, product_id):
    if not request.user.is_superuser:
        return redirect('home')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.category_id = request.POST.get('category')
        product.price = request.POST.get('price')
        product.description = request.POST.get('description')
        product.unit = request.POST.get('unit')
        product.is_available = request.POST.get('is_available') == 'on'
        product.save()
        messages.success(request, f'Товар "{product.name}" обновлен')
        return redirect('admin_products')
    
    context = {
        'product': product,
        'categories': Category.objects.all(),
    }
    return render(request, 'shop/admin_product_form.html', context)

@login_required
def admin_product_delete(request, product_id):
    if not request.user.is_superuser:
        return redirect('home')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Товар "{product_name}" удален')
        return redirect('admin_products')
    
    return render(request, 'shop/admin_product_confirm_delete.html', {'product': product})

@login_required
def admin_sales(request):
    """Статистика продаж"""
    if not request.user.is_superuser:
        return redirect('home')
    
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status='completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    product_sales = OrderItem.objects.values('product__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price_at_time'))
    ).order_by('-total_revenue')
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'product_sales': product_sales,
    }
    return render(request, 'shop/admin_sales.html', context)

@login_required
def admin_categories(request):
    """Управление категориями"""
    if not request.user.is_superuser:
        return redirect('home')
    
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'shop/admin_categories.html', context)