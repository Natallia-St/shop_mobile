from django.shortcuts import render

# Create your views here.
import operator

from functools import reduce
from itertools import chain

from django.db import transaction
from django.db.models import Q
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.views.generic import DetailView, View

from .models import Category, Customer, Cart, CartProduct, Product, Shops, Logo, HowToOrder, HowToPay, Review
from .mixins import CartMixin
from .forms import OrderForm, LoginForm, RegistrationForm, ReviewForm
from .utils import recalc_cart
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from specs.models import ProductFeatures
from django.shortcuts import get_object_or_404

# Если  нужно выполнить более сложные запросы (например, запросы с операторами ИЛИ),
# можyj использовать объекты Q.
class MyQ(Q):
    default = 'OR'


class BaseView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        products = Product.objects.all()
        logo = Logo.objects.all()
        shop = Shops.objects.all()
        info = HowToOrder.objects.all()
        query = self.request.GET.get('search')

        # Создаем экземпляр класса
        paginator = Paginator(products, 2)
        # Получаем запрос, в которм есть page.
        page = request.GET.get('page')
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            # Если страница не является целым числом,возвращаем первую страницу.
            page_obj = paginator.page(1)
        except EmptyPage:
            # Если номер страницы больше, чем общее количество страниц,
            # возвращаем последнюю.
            page_obj = paginator.page(paginator.num_pages)
        products = page_obj

        context = {
            'logo': logo,
            'categories': categories,
            'products': products,
            'shop': shop,
            'page_obj': page_obj,
            'cart': self.cart,
            'search': query,
            'info': info,
        }
        # возвращать результат, который будет отрисован браузером
        return render(request, 'base.html', context)


class ProductDetailView(CartMixin, DetailView):
    model = Product
    context_object_name = 'product'
    template_name = 'product_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = self.get_object().category.__class__.objects.all()
        context['cart'] = self.cart
        context['shop'] = Shops.objects.all()

        return context


class CategoryDetailView(CartMixin, DetailView, ):
    model = Category
    queryset = Category.objects.all()
    # Список объектов (задан с помощью атрибута context_object_name), который будет доступен по имени 'category'. Это
    # ваше собственное имя переменной контекста в шаблоне
    # Его потом можно  возвратить методом get_context_object_name
    context_object_name = 'category'
    template_name = 'category_detail.html'
    # paginate_by = 1
    slug_url_kwarg = 'slug'


    # Переопределяем метод get_context_data() для того,
    # чтобы в контексте (в переменной контекста) передавать шаблону дополнительные переменные.
    # Например список категорий в методе get_context_data передается по умолчанию.
    # Очень часто возникает необходимость передать нашему отображени дополнительный контекст. Допустим у нас есть категория,
    # просмотр которой мы реализуем с помощью класса DetailView.
    # Нам необходимо также получить контекст корзины и т.д.. Это реализует метод get_context_data.
    def get_context_data(self,  **kwargs):
        # 1. В первую очередь получаем базовую реализацию контекста
        context = super().get_context_data(**kwargs)
        # Получаем query, где в параметре запроса есть 'search'
        query = self.request.GET.get('search')
        # 2. Добавляем новую переменную к контексту и инициализируем её некоторым значением и 3. В конце метода
        # возвращаем рбновленный контекст
        context['product'] = Product.objects.all()
        # Возвращает экземпляр объекта, который используется для detail views.
        category = self.get_object()
        context['cart'] = self.cart
        # Из model = Category получаем данные
        context['categories'] = self.model.objects.all()
        context['shop'] = Shops.objects.all()

        # Если нет запроса или есть запрос но без параметра search - то выводим из категории все продукты
        if (not query and not self.request.GET) or query == '':
            # "главная_модель"."зависимая_модель"_set
            # С помощью выражения модель__свойство (два подчеркивания) можно использовать свойство главной модели
            # для фильтрации по объектам зависимой модели.
            context['category_products'] = category.product_set.all()
            # НЕ ПОЛУЧИЛОСЬ РЕАЛИЗОВАТЬ ЗДЕСЬ ПАГИНАЦИЮ
            # paginator = Paginator(context['category_products'], 1)
            # page = self.request.GET.get('page')
            # try:
            #     context['category_products'] = paginator.page(page)
            #
            # except PageNotAnInteger:
            #     # Если страница не является целым числом,возвращаем первую страницу.
            #     context['category_products'] = paginator.page(1)
            #
            #
            # except EmptyPage:
            #     # Если номер страницы больше, чем общее количество страниц,
            #     # возвращаем последнюю.
            #     context['category_products'] = paginator.page(paginator.num_pages)
            #     print('Это context page_obj', context['category_products'])
            #

            # print('CONTEXT', context)
            return context

        # Если есть запрос с параметром search
        if query:
            # Приводим значение в search к нижнему регистру
            query = str(query.lower())
            # Из категории выбираем те продукты, в которых поле "title_lower" равняется тому, что пришло в query
            products = category.product_set.filter(Q(title_lower__icontains=query))
            context['category_products'] = products
            return context

        #  фильтр с чекбоксом
        url_kwargs = {}
        for item in self.request.GET:

            # Если в фильтре выбрано более 1-го  value в одной характеристике (отправлен в реквесте список из value) -
            # добавляем value списком в словарь
            if len(self.request.GET.getlist(item)) > 1:
                url_kwargs[item] = self.request.GET.getlist(item)



            # Если в фильтре выбрано не более 1-го  value в характеристике (отправлено в реквесте) - добавляем value
            # в словарь
            else:
                url_kwargs[item] = self.request.GET.get(item)


        # Django Q Filter предоставляет формы фильтров (на основе начальной загрузки и jQuery) и утилиты для сложных
        # фильтров запросов. Форма фильтра динамически выбирает возможные поля модели django и вычисляет Q-Query
        # с заданными входными данными. результирующий набор запросов автоматически аннотируется полем и значениями
        # данного Q-Query.
        q_condition_queries = Q()
        for key, value in url_kwargs.items():
            # Добавляем в объект Q, value из словаря url_kwargs
            if isinstance(value, list):
                q_condition_queries.add(Q(**{'value__in': value}), Q.OR)
            else:
                q_condition_queries.add(Q(**{'value': value}), Q.OR)
            print("q_condition_queries", q_condition_queries)

        # Получаем данные из модели  ProductFeatures и фильтруем: выводим id всех товаров, у которых подходящие
        # характеристики, переданные в  q_condition_queries
        pf = ProductFeatures.objects.filter(
            q_condition_queries
        ).prefetch_related('category', 'feature').values('product_id')
        # Выводим все продукты из конкретной категории, которым подходят id из pf
        products = category.product_set.filter(id__in=[pf_['product_id'] for pf_ in pf])
        context['category_products'] = products

        return context


class AddToCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)

        user = self.request.user
        if user.is_authenticated:
            user = user
        else:

            # return HttpResponse(
            #     "Authorize to add product to an order.")
            return HttpResponseRedirect('/registration/')
            # form = RegistrationForm(request.POST or None)
            # categories = Category.objects.all()
            # context = {
            #     'form': form,
            #     'categories': categories,
            #     'cart': self.cart
            # }
            # return render(request, 'registration.html', context)

        cart_product, created = CartProduct.objects.get_or_create(
            user=self.cart.owner, cart=self.cart, product=product
        )
        if created:
            self.cart.products.add(cart_product)
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Товар успешно добавлен")
        return HttpResponseRedirect('/cart/')


class DeleteFromCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, product=product
        )
        self.cart.products.remove(cart_product)
        cart_product.delete()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Товар успешно удален")
        return HttpResponseRedirect('/cart/')


class ChangeQTYView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, product=product
        )
        qty = int(request.POST.get('qty'))
        cart_product.qty = qty
        cart_product.save()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Кол-во успешно изменено")
        return HttpResponseRedirect('/cart/')


class CartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        shop = Shops.objects.all()
        context = {
            'cart': self.cart,
            'categories': categories,
            'shop': shop
        }
        return render(request, 'cart.html', context)


# Зазлогиниться
class CheckoutView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        form = OrderForm(request.POST or None)
        shop = Shops.objects.all()
        context = {
            'cart': self.cart,
            'categories': categories,
            'form': form,
            'shop': shop
        }
        return render(request, 'checkout.html', context)


class MakeOrderView(CartMixin, View):
    # Атомарность - определяющее свойство транзакций базы данных. atomic позволяет нам создать блок кода,
    # в котором гарантируется атомарность базы данных. Если блок кода успешно завершен, изменения фиксируются
    # в базе данных. Если есть исключение, изменения отменяются.
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        customer = Customer.objects.get(user=request.user)
        # Проверяем на валидность форму с заказом
        if form.is_valid():
            new_order = form.save(commit=False)
            new_order.customer = customer
            new_order.first_name = form.cleaned_data['first_name']
            new_order.last_name = form.cleaned_data['last_name']
            new_order.phone = form.cleaned_data['phone']
            new_order.address = form.cleaned_data['address']
            new_order.buying_type = form.cleaned_data['buying_type']
            new_order.order_date = form.cleaned_data['order_date']
            new_order.comment = form.cleaned_data['comment']
            new_order.save()
            self.cart.in_order = True
            self.cart.save()
            new_order.cart = self.cart
            new_order.save()
            customer.orders.add(new_order)
            messages.add_message(request, messages.INFO, 'Спасибо за заказ! Менеджер с Вами свяжется')
            return HttpResponseRedirect('/')
        # Редирект на главную страницу
        return HttpResponseRedirect('/checkout/')

# Авторизация
class LoginView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        categories = Category.objects.all()
        shop = Shops.objects.all()
        context = {
            'form': form,
            'categories': categories,
            'cart': self.cart,
            'shop': shop
        }
        return render(request, 'login.html', context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(
                username=username, password=password
            )
            if user:
                login(request, user)
                return HttpResponseRedirect('/')
        categories = Category.objects.all()
        context = {
            'form': form,
            'cart': self.cart,
            'categories': categories
        }
        return render(request, 'login.html', context)


# Регистрация
class RegistrationView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        categories = Category.objects.all()
        shop = Shops.objects.all()
        context = {
            'form': form,
            'categories': categories,
            'cart': self.cart,
            'shop': shop
        }
        return render(request, 'registration.html', context)

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.username = form.cleaned_data['username']
            new_user.email = form.cleaned_data['email']
            new_user.first_name = form.cleaned_data['first_name']
            new_user.last_name = form.cleaned_data['last_name']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            Customer.objects.create(
                user=new_user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address']
            )
            user = authenticate(
                username=new_user.username, password=form.cleaned_data['password']
            )
            login(request, user)
            return HttpResponseRedirect('/')
        categories = Category.objects.all()
        context = {
            'form': form,
            'categories': categories,
            'cart': self.cart
        }
        return render(request, 'registration.html', context)


# Магазины
def ShopsView(request):
    shop = Shops.objects.all()
    categories = Category.objects.all()
    context = {
        'shop': shop,
        'categories': categories,

    }

    return render(request, 'shop.html', context)


# Информация о том, как заказать
def HowToOrderView(request):
    info = HowToOrder.objects.all()
    categories = Category.objects.all()
    shop = Shops.objects.all()
    context = {
        'info': info,
        'categories': categories,
        'shop': shop

    }

    return render(request, 'howtoorder.html', context)


# Информация о том, как заплатить
def HowToPayView(request):
    info = HowToPay.objects.all()
    categories = Category.objects.all()
    shop = Shops.objects.all()
    context = {
        'info': info,
        'categories': categories,
        'shop': shop

    }
#
    return render(request, 'howtopay.html', context)


# Обратная связь
class ReviewView(View):

    def get(self, request, *args, **kwargs):
        form = ReviewForm(request.POST or None)
        categories = Category.objects.all()
        shop = Shops.objects.all()
        context = {
            'form': form,
            'categories': categories,
            # 'cart': self.cart,
            'shop': shop
        }
        return render(request, 'review.html', context )

    def post(self, request, *args, **kwargs):
        form = ReviewForm(request.POST or None)
        categories = Category.objects.all()
        # shop = Shops.objects.all()
        if form.is_valid():
            review = Review(
            title = form.cleaned_data['title'],
            name_user = form.cleaned_data['name_user'],
            phone = form.cleaned_data['phone'],
            email = form.cleaned_data['email'],
            describe = form.cleaned_data['describe']
                )

            review.save()



            return HttpResponseRedirect('/')

        context = {
            'form': form,
            'categories': categories,
            # 'shop': shop

        }
        return render(request, 'registration.html', context)
