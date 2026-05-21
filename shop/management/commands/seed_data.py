from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shop.models import *
from datetime import date, timedelta
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными'
    
    def handle(self, *args, **options):
        self.stdout.write('Начинаем заполнение базы данных...')
        
        # ==================== 1. КАТЕГОРИИ ====================
        self.stdout.write('1. Создание категорий...')
        categories = ['Торты', 'Пирожные', 'Печенье', 'Макаруны', 'Эклеры', 'Капкейки', 'Пряники']
        category_objs = []
        for cat_name in categories:
            cat, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={'description': f'Раздел {cat_name.lower()}'}
            )
            category_objs.append(cat)
            if created:
                self.stdout.write(f'   - Создана категория: {cat_name}')
        
        # ==================== 2. ТОВАРЫ ====================
        self.stdout.write('2. Создание товаров...')
        products_data = [
            # Торты
            ('Наполеон', 'Торты', 450.00, 'Классический слоеный торт с заварным кремом', 'pcs', True),
            ('Медовик', 'Торты', 500.00, 'Медовый торт с нежным сметанным кремом', 'pcs', True),
            ('Красный бархат', 'Торты', 550.00, 'Торт с ярким красным цветом и сливочным сыром', 'pcs', True),
            ('Прага', 'Торты', 480.00, 'Шоколадный торт с масляным кремом', 'pcs', True),
            ('Чизкейк', 'Торты', 520.00, 'Нежный творожный торт с ягодами', 'pcs', True),
            # Пирожные
            ('Картошка', 'Пирожные', 80.00, 'Пирожное из бисквитной крошки', 'pcs', True),
            ('Корзиночка', 'Пирожные', 90.00, 'Песочная корзиночка с кремом', 'pcs', True),
            # Печенье
            ('Овсяное', 'Печенье', 120.00, 'Домашнее овсяное печенье с изюмом', 'kg', True),
            ('Песочное', 'Печенье', 150.00, 'Рассыпчатое песочное печенье', 'kg', True),
            # Макаруны
            ('Макарун классический', 'Макаруны', 150.00, 'Французское миндальное пирожное', 'pcs', True),
            ('Макарун шоколадный', 'Макаруны', 160.00, 'Шоколадный макарун с ганашем', 'pcs', True),
            # Эклеры
            ('Эклер заварной', 'Эклеры', 120.00, 'Заварное пирожное с ванильным кремом', 'pcs', True),
            ('Эклер шоколадный', 'Эклеры', 130.00, 'Шоколадный эклер', 'pcs', True),
        ]
        
        for name, cat_name, price, desc, unit, available in products_data:
            category = Category.objects.get(name=cat_name)
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'unit': unit,
                    'price': price,
                    'description': desc,
                    'is_available': available,
                    'created_at': timezone.now() - timedelta(days=random.randint(1, 30))
                }
            )
            if created:
                self.stdout.write(f'   - Создан товар: {name} ({price} руб.)')
        
        # ==================== 3. ИНГРЕДИЕНТЫ (для статистики) ====================
        self.stdout.write('3. Создание ингредиентов...')
        ingredients_data = [
            ('Мука', 'кг', 1.50),
            ('Сахар', 'кг', 2.00),
            ('Масло сливочное', 'кг', 8.00),
            ('Яйца', 'шт', 0.50),
            ('Мед', 'кг', 10.00),
            ('Шоколад', 'кг', 15.00),
            ('Сливки', 'л', 5.00),
            ('Миндальная мука', 'кг', 20.00),
        ]
        
        for name, unit, cost in ingredients_data:
            ing, created = Ingredient.objects.get_or_create(
                name=name,
                defaults={'unit': unit, 'cost_per_unit': cost}
            )
        
        # ==================== 4. НОВОСТИ ====================
        self.stdout.write('4. Создание новостей...')
        news_data = [
            {
                'title': 'Открытие новой кондитерской!',
                'summary': 'Мы рады сообщить об открытии нового филиала в центре города',
                'content': 'Дорогие клиенты! 1 июня мы открываем новую кондитерскую на проспекте Независимости. Ждем вас на дегустацию!',
                'is_published': True
            },
            {
                'title': 'Новая коллекция тортов ко Дню Рождения',
                'summary': 'Представляем новую линейку праздничных тортов',
                'content': 'Теперь вы можете заказать торт с любым дизайном. 5% скидка на первый заказ!',
                'is_published': True
            },
            {
                'title': 'Акция: каждому 10-му покупателю подарок!',
                'summary': 'Участвуйте в розыгрыше призов',
                'content': 'Каждый 10-й покупатель получает сертификат на 20% скидку. Акция действует до конца месяца.',
                'is_published': True
            },
            {
                'title': 'Мастер-класс по приготовлению макарунов',
                'summary': 'Приглашаем на кулинарный мастер-класс',
                'content': 'В эту субботу проведем мастер-класс по приготовлению французских макарунов.',
                'is_published': True
            },
        ]
        
        for news_item in news_data:
            news, created = News.objects.get_or_create(
                title=news_item['title'],
                defaults={
                    'summary': news_item['summary'],
                    'content': news_item['content'],
                    'is_published': news_item['is_published'],
                    'created_at': timezone.now() - timedelta(days=random.randint(1, 60))
                }
            )
            if created:
                self.stdout.write(f'   - Создана новость: {news_item["title"]}')
        
        # ==================== 5. ПРОМОКОДЫ ====================
        self.stdout.write('5. Создание промокодов...')
        now = timezone.now()
        promocodes_data = [
            {'code': 'SWEET10', 'discount': 10, 'valid_days': 30, 'active': True},
            {'code': 'BIRTHDAY', 'discount': 15, 'valid_days': 60, 'active': True},
            {'code': 'WELCOME', 'discount': 20, 'valid_days': 14, 'active': True},
            {'code': 'OLDSALE', 'discount': 5, 'valid_days': -30, 'active': False},  # архивный
            {'code': 'EXPIRE2023', 'discount': 25, 'valid_days': -365, 'active': False},  # архивный
        ]
        
        for promo in promocodes_data:
            PromoCode.objects.get_or_create(
                code=promo['code'],
                defaults={
                    'discount_percent': promo['discount'],
                    'valid_from': now,
                    'valid_to': now + timedelta(days=promo['valid_days']) if promo['valid_days'] > 0 else now - timedelta(days=-promo['valid_days']),
                    'is_active': promo['active'],
                    'max_uses': random.randint(1, 50),
                    'used_count': random.randint(0, 10)
                }
            )
            self.stdout.write(f'   - Создан промокод: {promo["code"]}')
        
        # ==================== 6. ВАКАНСИИ ====================
        self.stdout.write('6. Создание вакансий...')
        vacancies_data = [
            {
                'title': 'Кондитер',
                'description': 'Приготовление тортов, пирожных, десертов',
                'requirements': 'Опыт работы от 1 года, знание рецептур',
                'salary': 'от 1500 BYN',
                'is_active': True
            },
            {
                'title': 'Пекарь',
                'description': 'Выпечка хлебобулочных изделий',
                'requirements': 'Опыт работы, знание технологического процесса',
                'salary': 'от 1200 BYN',
                'is_active': True
            },
            {
                'title': 'Продавец-консультант',
                'description': 'Консультирование покупателей, обслуживание кассы',
                'requirements': 'Коммуникабельность, знание ПК',
                'salary': 'от 1000 BYN',
                'is_active': True
            },
            {
                'title': 'Курьер',
                'description': 'Доставка заказов по городу',
                'requirements': 'Наличие автомобиля, права категории B',
                'salary': 'от 900 BYN + бонусы',
                'is_active': False
            },
        ]
        
        for vac in vacancies_data:
            vacancy, created = Vacancy.objects.get_or_create(
                title=vac['title'],
                defaults={
                    'description': vac['description'],
                    'requirements': vac['requirements'],
                    'salary': vac['salary'],
                    'is_active': vac['is_active'],
                    'created_at': timezone.now() - timedelta(days=random.randint(1, 90))
                }
            )
            if created:
                self.stdout.write(f'   - Создана вакансия: {vac["title"]}')
        
        # ==================== 7. ТЕРМИНЫ ДЛЯ СЛОВАРЯ ====================
        self.stdout.write('7. Создание словаря терминов...')
        glossary_data = [
            {'term': 'Макарун', 'definition': 'Французское миндальное пирожное с начинкой'},
            {'term': 'Эклер', 'definition': 'Заварное пирожное с кремом внутри'},
            {'term': 'Ганаш', 'definition': 'Шоколадный крем на основе сливок'},
            {'term': 'Бисквит', 'definition': 'Воздушное тесто для коржей тортов'},
            {'term': 'Крем-чиз', 'definition': 'Крем на основе сливочного сыра'},
            {'term': 'Карамелизация', 'definition': 'Процесс нагревания сахара для получения карамели'},
            {'term': 'Темперирование', 'definition': 'Процесс нагревания и охлаждения шоколада'},
        ]
        
        for item in glossary_data:
            term, created = GlossaryTerm.objects.get_or_create(
                term=item['term'],
                defaults={
                    'definition': item['definition'],
                    'added_date': timezone.now() - timedelta(days=random.randint(1, 365))
                }
            )
            if created:
                self.stdout.write(f'   - Создан термин: {item["term"]}')
        
        # ==================== 8. КЛИЕНТЫ И ПОЛЬЗОВАТЕЛИ ====================
        self.stdout.write('8. Создание клиентов...')
        names = ['Иван Петров', 'Анна Сидорова', 'Дмитрий Иванов', 'Елена Козлова', 'Сергей Морозов',
                 'Ольга Новикова', 'Алексей Воробьев', 'Мария Лебедева', 'Павел Соколов', 'Татьяна Кузнецова']
        
        client_objs = []
        for i, name in enumerate(names):
            # Создаем пользователя
            username = f'client_{i+1}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'password': 'pbkdf2_sha256$...'  # пароль будет "password123"
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            
            # Создаем клиента
            age_days = random.randint(6570, 25550)  # 18-70 лет
            client, created = Client.objects.get_or_create(
                user=user,
                defaults={
                    'name': name,
                    'phone': f'+375 (29) {random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}',
                    'email': user.email,
                    'address': f'ул. {random.choice(["Сладкая", "Минская", "Фрунзе", "Пушкина"])}, {random.randint(1,100)}',
                    'date_of_birth': date.today() - timedelta(days=age_days),
                    'registered_at': timezone.now() - timedelta(days=random.randint(1, 365)),
                    'total_spent': 0
                }
            )
            client_objs.append(client)
            if created:
                self.stdout.write(f'   - Создан клиент: {name}')
        
        # ==================== 9. ОТЗЫВЫ ====================
        self.stdout.write('9. Создание отзывов...')
        products_list = list(Product.objects.all())
        review_texts = [
            'Очень вкусно! Обязательно закажу еще!',
            'Отличное качество, свежие продукты',
            'Немного дороговато, но вкус отличный',
            'Быстрая доставка, вежливый курьер',
            'Могло быть и лучше, но в целом неплохо',
            'Лучшая кондитерская в городе!',
            'Заказывала торт на день рождения - восторг!',
            'Макаруны просто божественные',
            'Эклеры тают во рту',
            'Спасибо за вашу работу!'
        ]
        
        for i, client in enumerate(client_objs[:8]):  # первые 8 клиентов оставляют отзывы
            if products_list:
                product = random.choice(products_list)
                review, created = Review.objects.get_or_create(
                    client=client,
                    product=product,
                    defaults={
                        'rating': random.randint(4, 5),
                        'text': random.choice(review_texts),
                        'created_at': timezone.now() - timedelta(days=random.randint(1, 100))
                    }
                )
                if created:
                    self.stdout.write(f'   - Создан отзыв от {client.name}')
        
        # ==================== 10. ЗАКАЗЫ ====================
        self.stdout.write('10. Создание заказов и продаж...')
        total_sales = 0
        
        for client in client_objs[:6]:  # первые 6 клиентов делают заказы
            num_orders = random.randint(1, 3)
            for _ in range(num_orders):
                # Создаем заказ
                order_date = timezone.now() - timedelta(days=random.randint(1, 180))
                order = Order.objects.create(
                    client=client,
                    order_date=order_date,
                    delivery_date=order_date + timedelta(days=random.randint(1, 3)),
                    status=random.choice(['completed', 'delivering', 'confirmed']),
                    delivery_address=client.address,
                    total_amount=0
                )
                
                # Добавляем товары в заказ
                order_total = 0
                num_items = random.randint(1, 4)
                products_in_order = random.sample(products_list, min(num_items, len(products_list)))
                
                for product in products_in_order:
                    quantity = random.randint(1, 3)
                    subtotal = float(product.price) * quantity
                    order_total += subtotal
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price_at_time=float(product.price)
                    )
                
                # Применяем случайный промокод
                if random.random() < 0.3:  # 30% заказов с промокодом
                    promos = PromoCode.objects.filter(is_active=True)
                    if promos.exists():
                        promo = random.choice(promos)
                        order.promo_code = promo
                        discount = promo.discount_percent / 100
                        order_total = order_total * (1 - discount)
                        promo.used_count += 1
                        promo.save()
                
                order.total_amount = order_total
                order.save()
                total_sales += order_total
                
                # Обновляем общую сумму клиента
                if order.status == 'completed':
                    client.total_spent = float(client.total_spent) + order_total
                    client.save()
                
                self.stdout.write(f'   - Создан заказ #{order.id} на сумму {order_total:.2f} руб.')
        
        # ==================== 11. ИНФОРМАЦИЯ О КОМПАНИИ ====================
        self.stdout.write('11. Создание информации о компании...')
        company_info = [
            {'key': 'Год основания', 'value': '2020'},
            {'key': 'Адрес главного офиса', 'value': 'г. Минск, ул. Сладкая, 15'},
            {'key': 'Режим работы', 'value': 'Пн-Вс: 09:00 - 21:00'},
            {'key': 'Телефон для справок', 'value': '+375 (17) 123-45-67'},
            {'key': 'Email для заказов', 'value': 'order@sweetlife.by'},
            {'key': 'Количество магазинов', 'value': '5 филиалов по городу'},
        ]
        
        for info in company_info:
            CompanyInfo.objects.get_or_create(
                key=info['key'],
                defaults={'value': info['value']}
            )
            self.stdout.write(f'   - Добавлено: {info["key"]}')
        
        # ==================== 12. СОТРУДНИКИ И КОНТАКТЫ ====================
        self.stdout.write('12. Создание сотрудников и контактов...')
        employees_data = [
            {'name': 'Анна Кондитерская', 'position': 'confectioner', 'phone': '+375 (29) 111-11-11', 'email': 'anna@sweetlife.by', 'dob_days': 9125, 'responsibilities': 'Создание новых рецептов, контроль качества'},
            {'name': 'Олег Менеджерский', 'position': 'manager', 'phone': '+375 (29) 222-22-22', 'email': 'oleg@sweetlife.by', 'dob_days': 10950, 'responsibilities': 'Управление персоналом, решение организационных вопросов'},
            {'name': 'Иван Доставляев', 'position': 'courier', 'phone': '+375 (29) 333-33-33', 'email': 'ivan@sweetlife.by', 'dob_days': 7300, 'responsibilities': 'Доставка заказов клиентам'},
            {'name': 'Мария Админская', 'position': 'admin_shop', 'phone': '+375 (29) 444-44-44', 'email': 'maria@sweetlife.by', 'dob_days': 9490, 'responsibilities': 'Администрирование сайта, работа с заказами'},
        ]
        
        for emp_data in employees_data:
            employee, created = Employee.objects.get_or_create(
                name=emp_data['name'],
                defaults={
                    'position': emp_data['position'],
                    'phone': emp_data['phone'],
                    'email': emp_data['email'],
                    'date_of_birth': date.today() - timedelta(days=emp_data['dob_days']),
                    'hire_date': date.today() - timedelta(days=random.randint(100, 1000)),
                    'description': f'{emp_data["position"]} с большим опытом'
                }
            )
            if created:
                self.stdout.write(f'   - Создан сотрудник: {emp_data["name"]}')
            
            # Создаем контакты для сотрудников
            Contact.objects.get_or_create(
                employee=employee,
                defaults={
                    'work_phone': emp_data['phone'],
                    'work_email': emp_data['email'],
                    'responsibilities': emp_data['responsibilities']
                }
            )
        
        # ==================== 13. ИТОГИ ====================
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('✅ БАЗА ДАННЫХ УСПЕШНО ЗАПОЛНЕНА!'))
        self.stdout.write('='*50)
        self.stdout.write(f'\n📊 СТАТИСТИКА:')
        self.stdout.write(f'   - Категорий: {Category.objects.count()}')
        self.stdout.write(f'   - Товаров: {Product.objects.count()}')
        self.stdout.write(f'   - Новостей: {News.objects.count()}')
        self.stdout.write(f'   - Промокодов: {PromoCode.objects.count()}')
        self.stdout.write(f'   - Вакансий: {Vacancy.objects.count()}')
        self.stdout.write(f'   - Терминов: {GlossaryTerm.objects.count()}')
        self.stdout.write(f'   - Клиентов: {Client.objects.count()}')
        self.stdout.write(f'   - Отзывов: {Review.objects.count()}')
        self.stdout.write(f'   - Заказов: {Order.objects.count()}')
        self.stdout.write(f'   - Сотрудников: {Employee.objects.count()}')
        self.stdout.write(f'   - Общая сумма продаж: {total_sales:.2f} руб.')
        self.stdout.write('='*50)