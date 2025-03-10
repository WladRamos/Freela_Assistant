from django.db import models
from django.contrib.auth.models import AbstractUser

class TipoUsuario(models.TextChoices):
    ADMINISTRADOR = "Administrador"
    USUARIO = "Usuario"

class TipoPagamento(models.TextChoices):
    HORA = "Hora"
    FIXO = "Fixo"

class User(AbstractUser):
    tipo_usuario = models.CharField(max_length=20, choices=TipoUsuario.choices, default=TipoUsuario.USUARIO)
    preco_hora_min = models.FloatField(null=True, blank=True)
    preco_fixo_min = models.FloatField(null=True, blank=True)

class Chat(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')
    data = models.DateTimeField(auto_now_add=True)

class Mensagem(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='mensagens')
    conteudo = models.TextField()
    data = models.DateTimeField(auto_now_add=True)

class RespostaAssistente(models.Model):
    mensagem = models.OneToOneField(Mensagem, on_delete=models.CASCADE, related_name='resposta_assistente')
    conteudo = models.TextField()
    data = models.DateTimeField(auto_now_add=True)

class Habilidade(models.Model):
    nome = models.CharField(max_length=100)

class UsuarioHabilidade(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habilidades')
    habilidade = models.ForeignKey(Habilidade, on_delete=models.CASCADE)

class ProjetoHistorico(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projetos')
    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    tipo_pagamento = models.CharField(max_length=10, choices=TipoPagamento.choices)
    valor_pagamento = models.FloatField()

class ProjetoHabilidade(models.Model):
    projeto = models.ForeignKey(ProjetoHistorico, on_delete=models.CASCADE, related_name='habilidades')
    habilidade = models.ForeignKey(Habilidade, on_delete=models.CASCADE)
