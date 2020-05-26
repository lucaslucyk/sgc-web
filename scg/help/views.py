from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, \
    permission_required, user_passes_test
from django.contrib import messages
from django.db.models import Q

from .models import Help
from .forms import HelpForm


# Create your views here.
@login_required
def help_create(request, context=None):
    """ Allows create a specific Help. """

    template = "apps/help/create.html"

    form = HelpForm(request.POST if request.method == 'POST' else None)
    context = context or {'form': form}

    if request.method == 'POST':
        if not form.is_valid():
            messages.error(request, "Error en datos del formulario.")
            return render(request, template, context)

        _help = form.save(commit=False)
        _help.save()

        messages.success(request, "Se ha generado el punto de ayuda.")
        #return redirect('saldo_update', pk=new_saldo.id)

    return render(request, template, context)


@login_required
def help_update(request, pk, context=None):
    """ Allows updating the data of a Help. """

    template = 'apps/help/create.html'
    _help = get_object_or_404(Help, pk=pk)

    if request.method == 'POST':
        form = HelpForm(request.POST, instance=_help)
        context = context or {'form': form}

        if not form.is_valid():
            messages.error(request, 'Error de formulario.')
            return render(request, template, context)

        _help = form.save(commit=False)
        _help.save()

        messages.success(request, "Se actualizó el punto de ayuda.")
        return redirect('help_update', pk=_help.id)

    form = HelpForm(instance=_help)
    context = {'form': form}

    return render(request, template, context)

@login_required
def help_detail(request, pk, context=None):
    """ Allows view detail of a specific Help. """

    template = 'apps/help/detail.html'
    _help = get_object_or_404(Help, pk=pk)

    context = {"help_detail": _help,}
    return render(request, template, context)

@login_required
def help_print(request, pk, context=None):
    """ Allows print detail of a specific Help. """

    template = 'apps/help/print.html'
    _help = get_object_or_404(Help, pk=pk)

    context = {"help_detail": _help,}
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
