from django import forms
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget

from .models import Help


class HelpForm(forms.ModelForm):
    attrs = {
        'class': 'form-control',
    }

    title = forms.CharField()
    slug = forms.SlugField(max_length=250, required=False)
    tags = forms.CharField()
    short_description = forms.CharField()
    content = forms.CharField(widget=CKEditorUploadingWidget())

    title.widget.attrs.update(attrs)
    tags.widget.attrs.update(attrs)
    short_description.widget.attrs.update(attrs)
    content.widget.attrs.update(attrs)

    class Meta:
        model = Help
        fields = '__all__'
