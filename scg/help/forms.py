from django import forms
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget

from .models import Help


class HelpForm(forms.ModelForm):
    attrs = {
        'class': 'form-control',
    }

    title = forms.CharField()
    tags = forms.CharField()
    content = forms.CharField(widget=CKEditorUploadingWidget())

    title.widget.attrs.update(attrs)
    tags.widget.attrs.update(attrs)
    content.widget.attrs.update(attrs)

    class Meta:
        model = Help
        fields = '__all__'
