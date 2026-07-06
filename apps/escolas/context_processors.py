def escola_context(request):
    vinculos_count = 0
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        vinculos_count = user.vinculos.filter(ativo=True, escola__ativa=True).count()
    return {
        'vinculo': getattr(request, 'vinculo', None),
        'escola': getattr(request, 'escola', None),
        'vinculos_count': vinculos_count,
    }
