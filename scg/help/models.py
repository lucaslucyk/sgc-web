from django.db import models
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.shortcuts import reverse

# from django.contrib.contenttypes import generic
# from django.contrib.contenttypes.models import ContentType


# Create your models here.

class Help(models.Model):
    """ Help for scg_app """

    title = models.TextField(unique=True, max_length=200, blank=True, null=True)
    tags = models.TextField(max_length=200, blank=True, null=True)
    short_description = models.TextField(max_length=200, blank=True, null=True)

    content = RichTextUploadingField(
        # extra_plugins=['uploadwidget', 'autoembed', 'youtube'],
        # external_plugin_resources=[(
        #     'youtube',
        #     '/static/ckeditor/ckeditor/youtube/',
        #     'plugin.js'
        # )]
    )

    # models = generic.GenericRelation(
    #     'MessageRecipient',
    #     content_type_field='recipient_content_type',
    #     object_id_field='recipient_id'
    #     )

    # class Meta:
    #     abstract = True

    def __str__(self):
        return self.title

    def get_edit_url(self):
        """ construct edit url from current object """
        return reverse('help_update', kwargs={"pk": self.id})
    
    def get_print_url(self):
        """ construct print url from current object """
        return reverse('help_print', kwargs={"pk": self.id})

    def get_delete_url(self):
        """ construct delete url from current object """
        return reverse(
            'confirm_delete',
            kwargs={"model": self.__class__.__name__, "pk": self.id})

    def pos_delete_url(self):
        """ construct pos delete url from current object """
        return reverse('periodos_view')
    
