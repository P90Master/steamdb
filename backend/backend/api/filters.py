from utils.filters import CustomOrderingFilter, FilterField


class GameOrderingFilter(CustomOrderingFilter):
    class Meta:
        ordering_param = 'ordering'

    total_recommendations = FilterField()
    #current_price = MethodFilterField(action='order_by_current_price')

    #def order_by_current_price(self, queryset, request):
    #    return queryset
