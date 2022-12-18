from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django_admin_geomap import GeoItem

# Mетод вернет текущую активную модель пользователя
User = get_user_model()


# Категории для продуктов
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Имя категории')
    image = models.ImageField(upload_to='category/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

    class Meta:
        ordering = ('name',)
        verbose_name = "Категория товаров"
        verbose_name_plural = "Категории товаров"


# Продукты
class Product(models.Model):
    category = models.ForeignKey('Category', verbose_name='Категория', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Наименование товара', unique=False)
    title_lower = models.CharField(max_length=255, verbose_name="Наим.товара в нижнем регистре_не изменять!" )#editable=False
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='product/', blank=True)
    description = models.TextField(verbose_name='Описание', null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена')
    features = models.ManyToManyField('specs.ProductFeatures', blank=True, related_name='features_for_product')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        # Для того, чтобы по Поиску искало и маленькими и большими буквами, добавляем поле title_lower, в котором приводим
        # все к нижнему регистру
        self.title_lower = self.title.lower() if self.title else None
        # Переопределение функции save() (для Product) перед сохранением данных в базе данных, чтобы добавить новые данные
        # или удалить некоторые данные, которые будут храниться в базе данных.
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    # Добавляем для товара  вывод характеристик (выводим в дельном виде о товаре)
    def get_features(self):
        return {f.feature.feature_name: ' '.join([f.value, f.feature.unit or ""]) for f in self.features.all()}

    class Meta:
        ordering = ('title',)
        verbose_name = "Товар"
        verbose_name_plural = "Товары"


# Продукты в корзине
class CartProduct(models.Model):
    user = models.ForeignKey('Customer', verbose_name='Покупатель', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Корзина', on_delete=models.CASCADE, related_name='related_products')
    product = models.ForeignKey('Product',  verbose_name='Товар', on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая цена')

    def __str__(self):
        return "Продукт: {} (для корзины)".format(self.product)

    def save(self, *args, **kwargs):
        self.final_price = self.qty * self.product.price
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Продукт в корзине"
        verbose_name_plural = "Продукты в корзине"


# Корзина
class Cart(models.Model):
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey('Customer', null=True, verbose_name='Владелец', on_delete=models.CASCADE)
    products = models.ManyToManyField('CartProduct', blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name='Общая цена')
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return 'Корзина: {}'.format(self.id)

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзина"


# Покупатель
class Customer(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Номер телефона', null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name='Адрес', null=True, blank=True)
    orders = models.ManyToManyField('Order', verbose_name='Заказы покупателя', related_name='related_order')

    def __str__(self):
        return "Покупатель: {} ".format(self.user)

    class Meta:
        verbose_name = "Покупатель"
        verbose_name_plural = "Покупатели"


# Комментарии для товара
# class Comment(models.Model):
#     client = models.ForeignKey('Customer', verbose_name="Пользователь", on_delete=models.CASCADE)
#     product = models.ForeignKey('Product', verbose_name="Товар", on_delete=models.CASCADE)
#     rating = models.FloatField(verbose_name="Оценка", null=True, blank=True)
#     text = models.TextField(verbose_name="Отзыв")
#     created = models.DateTimeField(
#         verbose_name="Дата написания", auto_now_add=True)
#
#     def __str__(self):
#         return self.text[:20]
#
#     class Meta:
#         verbose_name = "Отзыв"
#         verbose_name_plural = "Отзывы"



# Заказ
class Order(models.Model):
    # Создание перечня статусов заказов -  который доступен для выбора
    # Можно было реализовать и иначе - добавить отдельную модель и связать с этой, и кажется, что такой вариант лучше.
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    # Создание перечня способов доставки, который доступен для выбора
    # Можно было реализовать и иначе - добавить отдельную модель и связать с этой.
    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    # Статус заказа - добавляем названия статусов.
    STATUS_CHOICES = (
        (STATUS_NEW, 'Новый заказ'),
        (STATUS_IN_PROGRESS, 'Заказ в обработке'),
        (STATUS_READY, 'Заказ готов'),
        (STATUS_COMPLETED, 'Заказ выполнен')
    )

    # Способ доставки - добавляем название способов
    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовывоз'),
        (BUYING_TYPE_DELIVERY, 'Доставка')
    )

    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey('Customer', verbose_name='Покупатель', related_name='related_orders',
                                 on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, verbose_name='Имя')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    cart = models.ForeignKey('Cart', verbose_name='Корзина', on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=1024, verbose_name='Адрес', null=True, blank=True)
    status = models.CharField(
        max_length=100,
        verbose_name='Статус заказ',
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )
    buying_type = models.CharField(
        max_length=100,
        verbose_name='Тип заказа',
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_SELF
    )
    comment = models.TextField(verbose_name='Комментарий к заказу', null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, verbose_name='Дата создания заказа')
    order_date = models.DateField(verbose_name='Дата получения заказа', default=timezone.now)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


# Магазины
class Shops(models.Model):
    name = models.CharField(verbose_name="Наименование", max_length=80)
    address = models.CharField(verbose_name="Адрес", max_length=150)
    phone = models.CharField(verbose_name="Телефон", max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"


# Логотип
class Logo(models.Model):
    name = models.CharField(verbose_name="Наименование", max_length=80, default='1')
    image = models.ImageField( blank=True)

    def __str__(self):
        return self.name


# Информация, как заказать
class HowToOrder(models.Model):
    block = models.CharField(max_length=10, verbose_name='Номер блока информации')
    describe_order = models.TextField(verbose_name='Способы заказа')
    describe_delivery = models.TextField(verbose_name='Способы доставки')
    shop = models.ManyToManyField('Shops', verbose_name='Магазины')
    published = models.BooleanField(default=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.block

    def get_absolute_url(self):
        return reverse('howtoorder', kwargs={'slug': self.slug})


# Информация, как оплатить
class HowToPay(models.Model):
    block = models.CharField(max_length=10, verbose_name='Номер блока информации')
    describe_order = models.TextField(verbose_name='Способы оплаты')
    shop = models.ManyToManyField('Shops', verbose_name='Магазины')
    published = models.BooleanField(default=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.block

    def get_absolute_url(self):
        return reverse('howtopay', kwargs={'slug': self.slug})


# Обратная связь
class Review(models.Model):
    title = models.CharField(max_length=20, verbose_name='Краткое содержание обращения')
    name_user = models.CharField(max_length=10, verbose_name='Наименование орг./Имя, Фамилия')
    phone = models.CharField(max_length=30, verbose_name='Телефон для связи')
    email = models.CharField(max_length=30, verbose_name='email')
    describe = models.TextField(verbose_name='Текст обращения')


    def __str__(self):
        return self.title


