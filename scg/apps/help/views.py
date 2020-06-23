# -*- coding: utf-8 -*-

### built-in ###
#...

### third ###
#...

### django ###
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, \
    permission_required, user_passes_test
from django.contrib import messages
from django.db.models import Q

### own ###
from apps.scg_app.utils import unique_slug_generator
from apps.help.models import Help
from apps.help.forms import HelpForm

# Create your views here.
@login_required
def help_create(request, context=None):
    """ Allows create a specific Help. """

    template = "apps/help/create.html"

    form = HelpForm(request.POST if request.method == 'POST' else None)
    context = context or {'form': form}

    if request.method == 'POST':
        if not form.is_valid():
            #error is rendered in template
            return render(request, template, context)

        _help = form.save(commit=False)
        _help.slug = unique_slug_generator(_help, _help.title)
        _help.save()

        messages.success(request, "Se ha generado el punto de ayuda.")
        return redirect('help_detail', slug_text=_help.slug)

    return render(request, template, context)


@login_required
def help_update(request, slug_text, context=None):
    """ Allows updating the data of a Help. """

    template = 'apps/help/create.html'
    _help = get_object_or_404(Help, slug=slug_text)

    if request.method == 'POST':
        form = HelpForm(request.POST, instance=_help)
        context = context or {'form': form}

        if not form.is_valid():
            messages.error(request, 'Error de formulario.')
            return render(request, template, context)

        _help = form.save(commit=False)
        _help.save()

        messages.success(request, "Se actualizó el punto de ayuda.")
        return redirect('help_detail', slug_text=_help.slug)

    form = HelpForm(instance=_help)
    context = {'form': form}

    return render(request, template, context)

@login_required
def help_detail(request, slug_text, context=None):
    """ Allows view detail of a specific Help. """

    template = 'apps/help/detail.html'
    _help = get_object_or_404(Help, slug=slug_text)

    context = {"help_detail": _help}
    return render(request, template, context)

@login_required
def help_print(request, slug_text, context=None):
    """ Allows print detail of a specific Help. """

    template = 'apps/help/print.html'
    _help = get_object_or_404(Help, slug=slug_text)

    context = {"help_detail": _help}
    return render(request, template, context)


@login_required
def help_list(request, context=None):
    """ Allows list detail of a specific Help. """

    template = 'apps/help/list.html'
    
    qs = Q()
    if 'q' in request.GET:
        qs.add(Q(title__icontains=request.GET.get('q')), Q.OR)
        qs.add(Q(tags__icontains=request.GET.get('q')), Q.OR)
        qs.add(Q(short_description__icontains=request.GET.get('q')), Q.OR)

    _helps = Help.objects.filter(qs)

    context = {"help_list": _helps,}
    return render(request, template, context)
