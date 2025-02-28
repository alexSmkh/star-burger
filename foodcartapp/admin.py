from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django import forms

from .helpers.restaurant_helpers import get_available_restaurants
from .models import Order, OrderItem, Product
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem
from locations.models import Location
from star_burger.settings import ALLOWED_HOSTS


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]

    def save_model(self, request, obj, form, change):
        if not change or 'address' in form.changed_data:
            Location.create_location_by_address(form.cleaned_data['address'])
        super().save_model(request, obj, form, change)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ['product', 'quantity', 'product_price']
    extra = 0


class OrderForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = [
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'called_at',
            'delivered_at',
            'status',
            'payment_type',
            'comment',
            'processing_restaurant',
        ]

    def clean(self):
        if self.cleaned_data['processing_restaurant'] is None and self.cleaned_data['status'] != Order.PROCESS_STATUS:
            raise forms.ValidationError({'restaurant': 'Вы должны выбрать ресторан'})
        return self.cleaned_data


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderForm
    readonly_fields = ['price', 'created_at']
    inlines = [OrderItemInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.with_price().select_related('processing_restaurant')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        product_ids = obj.items.values_list('product_id', flat=True)
        restaurant_ids = list(map(lambda rest: rest.id, get_available_restaurants(product_ids)))
        form.base_fields['processing_restaurant'].queryset = Restaurant.objects.filter(id__in=restaurant_ids)
        return form

    def save_model(self, request, obj, form, change):
        if form.cleaned_data['processing_restaurant'] and form.cleaned_data['status'] == Order.PROCESS_STATUS:
            obj.status = Order.COOKING_STATUS

        if not change or 'address' in form.changed_data:
            Location.create_location_by_address(form.cleaned_data['address'])

        super().save_model(request, obj, form, change)

    def response_change(self, request, obj):
        res = super().response_post_save_change(request, obj)
        if 'next' in request.GET and url_has_allowed_host_and_scheme(request.GET['next'], ALLOWED_HOSTS):
            return HttpResponseRedirect(request.GET['next'])
        else:
            return res

    @admin.display(description='Сумма')
    def price(self, obj):
        return obj.price

    @admin.display(description='Рестораны')
    def available_restaurants(self, obj):
        return get_available_restaurants(obj.items.values_list('product_ids', flat=True))
