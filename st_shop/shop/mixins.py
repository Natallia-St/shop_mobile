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

