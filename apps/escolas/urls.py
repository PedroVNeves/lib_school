from django.urls import path

from . import views

urlpatterns = [
    path('selecionar/', views.EscolaSelecaoView.as_view(), name='escola-selecao'),
    path('trocar/', views.TrocarEscolaView.as_view(), name='escola-trocar'),

    path('admin/escolas/', views.EscolaListView.as_view(), name='escola-list'),
    path('admin/escolas/nova/', views.EscolaCreateView.as_view(), name='escola-create'),
    path('admin/escolas/<int:pk>/editar/', views.EscolaUpdateView.as_view(), name='escola-update'),
    path('admin/escolas/<int:pk>/toggle/', views.EscolaToggleAtivaView.as_view(), name='escola-toggle'),
]
