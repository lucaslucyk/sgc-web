from django.contrib import admin
from ckeditor.widgets import CKEditorWidget

from .models import Help
from .forms import HelpForm

@admin.register(Help)
class HelpAdmin(admin.ModelAdmin):
    form = HelpForm
    list_display = ('title', 'tags')

#admin.site.register(Post, PostAdmin)
# Register your models here.
