from django.contrib import admin
from .models import Settings
from .models import TradeMetrics
from .models import Orders
from .models import LastAnalysis
from .models import Ranks


class LastAnalysisAdmin(admin.ModelAdmin):
    list_display = ('market', 'timestamp', 'rating', 'score')
    search_fields = ('market', 'timestamp', 'rating', 'score')


class RankAdmin(admin.ModelAdmin):
    list_display = ('label', 'score')
    search_fields = ('label', 'score')


admin.site.register(Settings)
admin.site.register(TradeMetrics)
admin.site.register(Orders)
admin.site.register(LastAnalysis, LastAnalysisAdmin)
admin.site.register(Ranks, RankAdmin)
