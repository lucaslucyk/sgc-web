# -*- coding: utf-8 -*-

### built-in ###
#...

### third ###
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField

### django ###
from django.db import models
from django.shortcuts import reverse
# from django.contrib.contenttypes import generic
# from django.contrib.contenttypes.models import ContentType

### own ###
from apps.scg_app.utils import unique_slug_generator

class Help(models.Model):
    """ Help for scg_app """

    title = models.TextField(unique=True, max_length=200, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=250)
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

    class Meta:
        verbose_name = "Ayuda"
        verbose_name_plural = "Ayudas"

    # def save(self, *args, **kwargs):
    #     self.slug = unique_slug_generator(self, self.title)
    #     super().save(*args, **kwargs)

    def get_detail_url(self):
        """ construct edit url from current object """
        return reverse('help_detail', kwargs={"slug_text": self.slug})

    def get_edit_url(self):
        """ construct edit url from current object """
        return reverse('help_update', kwargs={"slug_text": self.slug})
    
    def get_print_url(self):
        """ construct print url from current object """
        return reverse('help_print', kwargs={"slug_text": self.slug})

    def get_delete_url(self):
        """ construct delete url from current object """
        return reverse(
            'confirm_delete',
            kwargs={"model": self.__class__.__name__, "pk": self.id})

    @property
    def pronombre(self):
        return "La"

    @property
    def get_str(self):
        return self.__str__()

    def pos_delete_url(self):
        """ construct pos delete url from current object """
        return reverse('help_list')

    def __str__(self):
        return self.title
    
