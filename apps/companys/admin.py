from django.contrib import admin
from companys.models import Company

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'creator', 'created')

admin.site.register(Company, CompanyAdmin)
