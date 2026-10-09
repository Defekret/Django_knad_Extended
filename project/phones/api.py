import json

from django.db.models import Avg, Count, Max, Min, Q
from django.http import HttpResponse, JsonResponse
from django.views import generic

from .forms import PhoneForm
from .models import Phone

PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
ORDER_FIELDS = ['id', 'price', 'rating', 'screen_size', 'camera_resolution', 'storage', 'brand', 'model_name']


def to_json(phone):
    return {
        'id': phone.id,
        'model_name': phone.model_name,
        'brand': phone.brand,
        'price': phone.price,
        'color': phone.color,
        'operation_system': phone.operation_system,
        'screen_size': phone.screen_size,
        'preview_text': phone.preview_text,
        'rating': phone.rating,
        'camera_resolution': phone.camera_resolution,
        'stock_quantity': phone.stock_quantity,
        'storage': phone.storage,
        'is_favorite': phone.is_favorite,
        'image': phone.image.url,
    }


def error(message, status=400):
    return JsonResponse({'error': message}, status=status)


def get_phone(pk):
    return Phone.objects.filter(pk=pk).first()


def page_response(request, phones):
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', PAGE_SIZE)), MAX_PAGE_SIZE)
    if page < 1 or page_size < 1:
        raise ValueError
    start = (page - 1) * page_size
    return JsonResponse({
        'total': phones.count(),
        'page': page,
        'page_size': page_size,
        'items': [to_json(phone) for phone in phones[start:start + page_size]],
    })


class PhoneListApi(generic.View):
    def get(self, request):
        params = request.GET
        phones = Phone.objects.all()
        try:
            if params.get('brand'):
                phones = phones.filter(brand__iexact=params['brand'])
            if params.get('os'):
                phones = phones.filter(operation_system__iexact=params['os'])
            if params.get('price_min'):
                phones = phones.filter(price__gte=float(params['price_min']))
            if params.get('price_max'):
                phones = phones.filter(price__lte=float(params['price_max']))
            if params.get('storage_min'):
                phones = phones.filter(storage__gte=int(params['storage_min']))
            if params.get('in_stock') == 'true':
                phones = phones.filter(stock_quantity__gt=0)
            if params.get('search'):
                search = params['search']
                phones = phones.filter(Q(model_name__icontains=search) | Q(brand__icontains=search))

            ordering = params.get('ordering', 'id')
            if ordering.lstrip('-') not in ORDER_FIELDS:
                return error('Нельзя сортировать по этому полю')

            return page_response(request, phones.order_by(ordering))
        except ValueError:
            return error('Неверное значение параметра')

    def post(self, request):
        try:
            data = json.loads(request.body)
        except ValueError:
            return error('Ожидается JSON')

        form = PhoneForm(data)
        if not form.is_valid():
            return JsonResponse({'errors': form.errors}, status=400)
        phone = form.save()
        return JsonResponse(to_json(phone), status=201)


class PhoneDetailApi(generic.View):
    def get(self, request, pk):
        phone = get_phone(pk)
        if not phone:
            return error('Телефон не найден', 404)
        return JsonResponse(to_json(phone))

    def patch(self, request, pk):
        phone = get_phone(pk)
        if not phone:
            return error('Телефон не найден', 404)
        try:
            data = json.loads(request.body)
        except ValueError:
            return error('Ожидается JSON')

        # поля, которые не прислали, остаются прежними
        old_data = to_json(phone)
        old_data.update(data)
        form = PhoneForm(old_data, instance=phone)
        if not form.is_valid():
            return JsonResponse({'errors': form.errors}, status=400)
        phone = form.save()
        return JsonResponse(to_json(phone))

    def delete(self, request, pk):
        phone = get_phone(pk)
        if not phone:
            return error('Телефон не найден', 404)
        phone.delete()
        return HttpResponse(status=204)


class PhoneCompareApi(generic.View):
    def get(self, request):
        try:
            phone_one = get_phone(int(request.GET.get('first', '')))
            phone_two = get_phone(int(request.GET.get('second', '')))
        except ValueError:
            return error('Укажите параметры first и second')
        if not phone_one or not phone_two:
            return error('Телефон не найден', 404)

        best_price = None
        best_screen_size = None
        best_camera = None
        best_storage = None

        if phone_one.price != phone_two.price:
            best_price = min(phone_one.price, phone_two.price)

        if phone_one.screen_size != phone_two.screen_size:
            best_screen_size = max(phone_one.screen_size, phone_two.screen_size)

        if phone_one.camera_resolution != phone_two.camera_resolution:
            best_camera = max(phone_one.camera_resolution, phone_two.camera_resolution)

        if phone_one.storage != phone_two.storage:
            best_storage = max(phone_one.storage, phone_two.storage)

        return JsonResponse({
            'phone_one': to_json(phone_one),
            'phone_two': to_json(phone_two),
            'best_price': best_price,
            'best_screen_size': best_screen_size,
            'best_camera': best_camera,
            'best_storage': best_storage,
        })


class FavoriteApi(generic.View):
    def post(self, request, pk):
        return self.set_favorite(pk, True)

    def delete(self, request, pk):
        return self.set_favorite(pk, False)

    def set_favorite(self, pk, value):
        phone = get_phone(pk)
        if not phone:
            return error('Телефон не найден', 404)
        phone.is_favorite = value
        phone.save()
        return JsonResponse(to_json(phone))


class FavoriteListApi(generic.View):
    def get(self, request):
        try:
            return page_response(request, Phone.objects.filter(is_favorite=True).order_by('id'))
        except ValueError:
            return error('Неверное значение параметра')


class StatsApi(generic.View):
    def get(self, request):
        stats = Phone.objects.aggregate(
            total=Count('id'),
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price'),
        )
        stats['in_stock'] = Phone.objects.filter(stock_quantity__gt=0).count()
        stats['brands'] = list(Phone.objects.values('brand').annotate(count=Count('id')).order_by('brand'))
        return JsonResponse(stats)


class HealthApi(generic.View):
    def get(self, request):
        Phone.objects.exists()
        return JsonResponse({'status': 'ok'})
