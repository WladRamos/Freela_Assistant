from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/chat_llm", views.chat_llm, name="chat_llm"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("profile", views.profile, name="profile"),
    path("editar_perfil", views.editar_perfil, name="editar_perfil"),
    path("get_trabalho/<int:trabalho_id>/", views.get_trabalho, name="get_trabalho"),
]