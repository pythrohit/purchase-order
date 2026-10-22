from django.contrib import admin
from .models import Category, ItemGroup, Item

admin.site.register(Category)
admin.site.register(ItemGroup)  
admin.site.register(Item)