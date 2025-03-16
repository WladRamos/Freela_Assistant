from django.db import models
from django.contrib.auth.models import AbstractUser
import unicodedata

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

    def __str__(self):
        return f"Chat {self.id} - {self.usuario.username} ({self.data.strftime('%d/%m/%Y %H:%M')})"

class Mensagem(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='mensagens')
    conteudo = models.TextField()
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensagem {self.id} - Chat {self.chat.id} ({self.data.strftime('%d/%m/%Y %H:%M')})"

class RespostaAssistente(models.Model):
    mensagem = models.OneToOneField(Mensagem, on_delete=models.CASCADE, related_name='resposta_assistente')
    conteudo = models.TextField()
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resposta à Mensagem {self.mensagem.id} ({self.data.strftime('%d/%m/%Y %H:%M')})"

class Habilidade(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        self.nome = self.normalizar_nome(self.nome)
        super().save(*args, **kwargs)

    @staticmethod
    def normalizar_nome(nome):
        nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
        return nome.upper()

    def __str__(self):
        return self.nome

class UsuarioHabilidade(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habilidades')
    habilidade = models.ForeignKey(Habilidade, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.usuario.username} - {self.habilidade.nome}"

class ProjetoHistorico(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projetos')
    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    tipo_pagamento = models.CharField(max_length=10, choices=TipoPagamento.choices)
    valor_pagamento = models.FloatField()

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username} ({self.tipo_pagamento})"

class ProjetoHabilidade(models.Model):
    projeto = models.ForeignKey(ProjetoHistorico, on_delete=models.CASCADE, related_name='habilidades')
    habilidade = models.ForeignKey(Habilidade, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.projeto.titulo} - {self.habilidade.nome}"
