from django.contrib import admin

from .models import *
from django_admin_geomap import ModelAdmin

# При регистрации в админке товара - поле со слагом заполняется автоматически
class ProductAdmin(admin.ModelAdmin):
    change_form_template = 'custom_admin/change_form.html'
    #exclude = ('features',)
    prepopulated_fields = {'slug': ('title',)}

admin.site.register(Category)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(Product, ProductAdmin)
admin.site.register(Shops)
admin.site.register(Logo)
admin.site.register(HowToOrder)
admin.site.register(HowToPay)
admin.site.register(Review)







