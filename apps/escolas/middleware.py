from .models import Vinculo


class EscolaContextMiddleware:
    """Resolve o vínculo/escola atual da sessão e anexa em request.vinculo/request.escola."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.vinculo = None
        request.escola = None

        vinculo_id = request.session.get('vinculo_id')
        if getattr(request, 'user', None) and request.user.is_authenticated and vinculo_id:
            vinculo = (
                Vinculo.objects.select_related('escola', 'usuario')
                .filter(pk=vinculo_id, usuario=request.user, ativo=True, escola__ativa=True)
                .first()
            )
            if vinculo:
                request.vinculo = vinculo
                request.escola = vinculo.escola
            else:
                del request.session['vinculo_id']

        return self.get_response(request)
