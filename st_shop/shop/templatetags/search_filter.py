#Создаем пользовательский фильтр с чекбоксом
from collections import defaultdict
from django import template
"""
Джанго выполняет escape-код HTML, генерируемый фильтрами. Мы используем функцию mark_safe, предоставляемую Джанго,
чтобы пометить результат как безопасный HTML для визуализации в шаблоне. По умолчанию, Джанго не пропустит ни однин
HTML-код. Единственным исключением являются переменные, помеченные как безопасные. Такое поведение предотвращает
появление потенциально опасного HTML-кода и позволяет создавать исключения, когда вы знаете, что вы возвращаете
безопасный HTML-код.
"""
from django.utils.safestring import mark_safe
from specs.models import ProductFeatures
# Создаем перем. register, которая является экземпляром template.Library,
# в котором зарегистрированы все теги и фильтры.
register = template.Library()

# Использование register.filter() в качестве декоратора
# Регистрация фильтра в экземпляре Library, чтобы сделать его доступным для  шаблонов Django
@register.filter
def product_spec(category):
    # получаем характеристики продукта, где продукты из категории=категории
    product_features = ProductFeatures.objects.filter(product__category=category)
    # словарь со значениями по умолчанию, в который передаем список, чтобы получить словарь списков -  в нем х-ки продукта
    feature_and_values = defaultdict(list)
    for product_feature in product_features:
        if product_feature.value not in feature_and_values[(product_feature.feature.feature_name, product_feature.feature.feature_filter_name)]:
            feature_and_values[
                (product_feature.feature.feature_name, product_feature.feature.feature_filter_name)
            ].append(product_feature.value)

    search_filter_body = """<div class="col-md-12">{}</div>"""
    mid_res = ""
    # Для каждой характеристики выводим  Имя х-ки и значение х-ки в чекбоксе
    for (feature_name, feature_filter_name), feature_values in feature_and_values.items():
        feature_name_html = f"""<p>{feature_name}</p>"""
        feature_values_res = ""
        # Для каждой х-ки
        for f_v in feature_values:
            mid_feature_values_res = \
                "<input type='checkbox' size='lg' name='{f_f_name}' value='{feature_name}'> {feature_name}</br>".format(
                    feature_name=f_v, f_f_name=feature_filter_name
                )
            feature_values_res += mid_feature_values_res
        feature_name_html += feature_values_res
        mid_res += feature_name_html + '<hr>'
    res = search_filter_body.format(mid_res)
    # Используем функцию mark_safe, чтобы возвратить HTML код
    return mark_safe(res)

