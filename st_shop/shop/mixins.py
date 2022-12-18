from django.views.generic import View

from .models import Cart, Customer

# Инициализация корзины
class CartMixin(View):

    def dispatch(self, request, *args, **kwargs):
        # Если получен запрос от авторизованного пользователя
        if request.user.is_authenticated:
            customer = Customer.objects.filter(user=request.user).first()
            print("CUSTOMER AUT", customer)
            if not customer:
                customer = Customer.objects.create(
                    user=request.user
                )
                print("Не понятный", customer)
            # Выводим товары в существующей корзине, которые в ней есть
            cart = Cart.objects.filter(owner=customer, in_order=False).first()
            # Eсли в переданном запросе отсутствует корзина мы создадим новую пустую корзину
            if not cart:
                cart = Cart.objects.create(owner=customer)
        # Заходим на сайт без авторизации и автоматически создается корзина для неавторизованного пользователя
        # в проекте запрещены покупки для неавторизованных пользователей, поэтому эта часть кода отключена
        else:
            cart = Cart.objects.filter(for_anonymous_user=True).first()

            if not cart:
                cart = Cart.objects.create(for_anonymous_user=True)
        self.cart = cart
        return super().dispatch(request, *args, **kwargs)


from decimal import Decimal
from django.conf import settings
from film import models


class Cart:

    def __init__ (self, request):
        """
        Инициализируем корзину
        """
        self.session = request.session  # получаем текущую сессию.
        # значение request.session мы передаём в динамическое свойство, чтобы сделать его доступным
        # для всех методов нашего класса Cart
        cart = self.session.get(settings.CART_SESSION_ID)  # в значение cart получаем значение CART_SESSION_ID
        if not cart:  # если в переданном значении сессии отсутствует корзина
            # мы создадим сессию с пустой корзиной, установив пустой словарь в сессии.
            # мы ожидаем, что наш словарь корзины будет использовать коды продуктов
            # в качестве ключей и словарь с количеством и ценой
            # в качестве значения для каждого ключа.
            # таким образом мы можем гарантировать, что продукт не будет добавлен в корзину более одного раза
            cart = self.session[settings.CART_SESSION_ID] = {}  # сохраняем новую корзину в сессии
        # обратите внимание, где в каком блоке мы передаём значение корзины
        # если сработает блок if мы передадим в self.cart пустую корзину
        # если же он не сработает, то в self.cart поместиться уже имеющаяся корзина
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False):

        product_id = str(product.id)  # id продукта используется в качестве ключа в словаре содержимого корзины

        if product_id not in self.cart:  # если id продукта отсутствует в корпзине
            self.cart[product_id] = {'quantity': 0,  # для указанного продукта устанавливаем количество 0

                                     # цену устанавливаем также в строковом значении
                                     # передавая из поля price
                                     'price': str(product.price)}
        if update_quantity:  # если мы указали на обновление количества продукта
            self.cart[product_id]['quantity'] = quantity
            # для количества продуктов устанавливаем значение, которое будет передано в quantity
        else:
            # в противном случае увеличиваем количество уже добавленного продукта на количество из quantity
            self.cart[product_id]['quantity'] += quantity
        # сохраняем изменения в сессии
        # для этого чуть ниже будет использоваться метод save()
        self.save()

    def save(self):
        # Данный метод мы будем использовать для обновления сессии
        # через код в строке 63 мы обновляем корзину для текущей сессии
        self.session[settings.CART_SESSION_ID] = self.cart
        # С помощью session.modified мы говорим "сессия self.session modified и должна быть сохранена"
        self.session.modified = True

    def remove(self, product):
        # в качестве параметров передаём ссылку на текущий объект корзины
        # данный метод будет удалять продукт из корзины, после чего будет вызыват метод save()
        # который сохранит изменения

        # получаем id нашего продукта, конвертируя в строку
        product_id = str(product.id)
        # если такой продукт в корзин
        if product_id in self.cart:
            # удаляем его из текущей корзины
            del self.cart[product_id]
            # и сохраняем изменения
            self.save()

    def __iter__ (self):
        """
        Перебор элементов в корзине и получение продуктов из базы данных.
        мы будем работать с фильмами, поэтому необходимо также верно указать путь до модели
        по которую мы будем использовать.
        """
        # получаем все id наших фильмов - 'nj не сами объекты, а просто елючи
        films_ids = self.cart.keys()
        # получаем все объекты фильмов на основе обнаруженных в корзине по id (квэрисет достаем по ай ди из словаря и находим какие товары им соответ-т
        films = models.Film.objects.filter(id__in=films_ids)
        # итерируемся по всем фильмам в полученном queryset фильмов
        for film in films:
            # в текущей корзине по ключу film.id, переходим к вложенному ключу product
            # передаём объект фильма в качестве значения, это словарь
            self.cart[str(film.id)]['product'] = film

        # после этого итерируемся по значениям корзины, (в корзине словарь, мы проходимся только по значениям - прас)
        for item in self.cart.values():
            # конвертируем значение price в децимал
            item['price'] = Decimal(item['price'])
            # создаём дополнительное значение конечной суммы, которое будет зависеть
            # от количество выбранных товаров
            # к примеру выбрано 2 товара по цене 1.50, total_price будет иметь значение 3.0
            item['total_price'] = item['price'] * item['quantity']
            # и возвращаем item
            yield item

    def len(self):
        # метод len будет возвращать
        # общее количество товаров для каждого продукта в значениях нашей корзины
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        # вернуть преобразованную к Decimal сумму товара
        # умноженную на количество quantity
        # для каждого объекта в значениях нашей корзины
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        # удаление корзины из сессии
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True
