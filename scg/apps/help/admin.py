### django
from django.contrib import admin
from ckeditor.widgets import CKEditorWidget

### own
from apps.help.models import Help
from apps.help.forms import HelpForm

@admin.register(Help)
class HelpAdmin(admin.ModelAdmin):
    form = HelpForm
    list_display = ('title', 'tags')

#admin.site.register(Post, PostAdmin)
# Register your models here.
