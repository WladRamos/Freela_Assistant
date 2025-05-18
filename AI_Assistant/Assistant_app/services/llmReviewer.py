from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Inicializar o modelo com streaming (essa LLM fará a revisão final)
review_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, streaming=True)

# Prompt para revisar e corrigir a resposta
review_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     """
Você é um revisor inteligente especializado em revisar respostas geradas por modelos de linguagem para freelancers da área de TI e programação.

Sua tarefa é:
1. Verificar se a resposta gerada está clara, útil e precisa com base na pergunta feita, no contexto de conversa, nas informações do usuário e nas evidências disponíveis.
2. Identificar e remover possíveis erros, ambiguidades, informações irrelevantes ou alucinações.
3. Manter a estrutura em Markdown da resposta, aprimorando quando necessário.
4. Garantir que a resposta está na mesma lingua que a pergunta do usuário, sem erros gramaticais ou de digitação.

Caso a resposta já esteja correta e útil, apenas replique a resposta original.
"""),
    ("user", 
     """
### Pergunta do usuário:
{user_question}

### Informações do usuário:
{user_info}

### Histórico de conversa:
{context}

### Contexto adicional do módulo:
{extra_context}

### Resposta gerada anteriormente:
{original_answer}
""")
])

# Chain que pode ser usado com .stream()
review_chain = review_prompt | review_llm

def stream_reviewed_answer(user_question, user_info, context, extra_context, original_answer):
    inputs = {
        "user_question": user_question,
        "user_info": user_info,
        "context": context,
        "extra_context": extra_context,
        "original_answer": original_answer,
    }
    for chunk in review_chain.stream(inputs):
        yield chunk.content
