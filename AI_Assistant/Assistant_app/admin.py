from django.contrib import admin
from .models import User, Chat, Mensagem, RespostaAssistente, Habilidade, UsuarioHabilidade, ProjetoHistorico, ProjetoHabilidade, Suspensao, Banimento

admin.site.register(User)
admin.site.register(Chat)
admin.site.register(Mensagem)  
admin.site.register(RespostaAssistente)
admin.site.register(Habilidade)
admin.site.register(UsuarioHabilidade)
admin.site.register(ProjetoHistorico)
admin.site.register(ProjetoHabilidade)
admin.site.register(Suspensao)
admin.site.register(Banimento)
