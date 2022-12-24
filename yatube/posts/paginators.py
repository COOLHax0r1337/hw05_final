from django.core.paginator import Paginator
# from . models import Post
# from . views import POST_LIMIT
from django.conf import settings


def paginate_page(request, queryset):
    paginator = Paginator(queryset, settings.POST_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }
