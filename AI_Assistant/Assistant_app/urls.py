from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/chat_llm", views.chat_llm, name="chat_llm"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("profile", views.profile, name="profile"),
    path("get_trabalho/<int:trabalho_id>/", views.get_trabalho, name="get_trabalho"),
    path("salvar_trabalho/", views.salvar_trabalho, name="salvar_trabalho"),
    path("excluir_trabalho/<int:trabalho_id>/", views.excluir_trabalho, name="excluir_trabalho"),
    path("salvar_precos/", views.salvar_precos, name="salvar_precos"),
    path("adicionar_habilidade/", views.adicionar_habilidade, name="adicionar_habilidade"),
    path("remover_habilidade/<int:habilidade_id>/", views.remover_habilidade, name="remover_habilidade"),
    path("chat/<int:chat_id>/", views.chat_view, name="chat_detail"),
    path("api/chats/", views.get_chats, name="get_chats"),
    path("api/chat/<int:chat_id>/messages/", views.get_chat_messages, name="get_chat_messages"),
    path("api/chat/<int:chat_id>/rename/", views.rename_chat, name="rename_chat"),
    path("api/chat/<int:chat_id>/delete/", views.delete_chat, name="delete_chat"),
    path("painel_admin/usuarios/", views.admin_user_list, name="admin_user_list"),
    path('painel_admin/usuarios/banir/', views.ban_user, name='ban_user'),
    path('painel_admin/usuarios/suspender/', views.suspend_user, name='suspend_user'),
    path("painel_admin/base-vetorial/", views.admin_vector_base, name="admin_vector_base"),
    path("painel_admin/base-vetorial/adicionar/", views.admin_adicionar_trabalho, name="add_vector_base"),
    path("painel_admin/base-vetorial/atualizar/", views.admin_atualizar_trabalho, name="update_vector_base"),
    path("painel_admin/base-vetorial/deletar/", views.admin_deletar_trabalhos, name="delete_vector_base"),
]