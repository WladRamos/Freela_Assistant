from django.db import models
from django.contrib.auth.models import AbstractUser
import unicodedata
from django.utils.timezone import now, timedelta

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
    nome = models.CharField(max_length=100, blank=True)
    data = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Salva primeiro para garantir o ID

        if not self.nome:  # Agora que temos um ID, podemos definir o nome
            self.nome = f"Chat {self.id}"
            super().save(update_fields=["nome"])  # Atualiza apenas o campo "nome"

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
    data = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username} ({self.tipo_pagamento})"

class ProjetoHabilidade(models.Model):
    projeto = models.ForeignKey(ProjetoHistorico, on_delete=models.CASCADE, related_name='habilidades')
    habilidade = models.ForeignKey(Habilidade, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.projeto.titulo} - {self.habilidade.nome}"

class Suspensao(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suspensoes')
    justificativa = models.TextField()
    data_inicio = models.DateTimeField(default=now)
    duracao_dias = models.IntegerField(default=0)
    duracao_horas = models.IntegerField(default=0)

    @property
    def data_fim(self):
        return self.data_inicio + timedelta(days=self.duracao_dias, hours=self.duracao_horas)

    @property
    def ativa(self):
        return now() < self.data_fim

    def __str__(self):
        return f"Suspensão de {self.usuario.username} até {self.data_fim.strftime('%d/%m/%Y %H:%M')}"

class Banimento(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='banimento')
    username_backup = models.CharField(max_length=150)
    email_backup = models.EmailField()
    justificativa = models.TextField()
    data = models.DateTimeField(default=now)

    def save(self, *args, **kwargs):
        if self.usuario and not self.username_backup:
            self.username_backup = self.usuario.username
            self.email_backup = self.usuario.email
        super().save(*args, **kwargs)

    def __str__(self):
        user_str = self.usuario.username if self.usuario else self.username_backup
        return f"Usuário {user_str} banido em {self.data.strftime('%d/%m/%Y %H:%M')}"