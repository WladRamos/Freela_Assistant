document.addEventListener('DOMContentLoaded', function(){
    let pathParts = window.location.pathname.replace(/\/$/, "").split("/");
    let currentChatId = pathParts.length > 2 && pathParts[1] === "chat" ? pathParts[2] : null;

    console.log("Chat atual:", currentChatId);

    // Função para adicionar uma mensagem ao chat
    function addMessage(content, className) {
        const messageArea = document.getElementById('message-area');
        const messageBox = document.createElement('div');
        messageBox.classList.add('message-box', className);
        messageBox.innerHTML = DOMPurify.sanitize(marked.parse(content));
        messageArea.appendChild(messageBox);
        setTimeout(() => { messageArea.scrollTop = messageArea.scrollHeight; }, 0);
    }

    // Carregar mensagens do chat selecionado
    function loadChatMessages(chatId) {
        fetch(`/api/chat/${chatId}/messages/`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('message-area').innerHTML = ""; // Limpa o chat
                data.mensagens.forEach(msg => {
                    addMessage(msg.conteudo, 'message-user');
                    if (msg.resposta) {
                        addMessage(msg.resposta.conteudo, 'message-response');
                    }
                });
            })
            .catch(error => console.error("Erro ao carregar mensagens:", error));
    }

    // Função para carregar os chats na barra lateral
    function loadChatList() {
        fetch('/api/chats/')
            .then(response => response.json())
            .then(data => {
                const chatList = document.getElementById("chat-list");
                chatList.innerHTML = ""; // Limpa a lista antes de recarregar

                data.chats.forEach(chat => {
                    let li = document.createElement("li");
                    li.textContent = chat.nome;
                    li.dataset.chatId = chat.id;
                    li.addEventListener("click", function () {
                        window.location.href = `/chat/${chat.id}/`;
                    });
                    chatList.appendChild(li);
                });
            })
            .catch(error => console.error("Erro ao carregar conversas:", error));
    }
    // Chamar a função ao carregar a página
    loadChatList();

    // Se estiver em um chat específico, carregar mensagens
    if (currentChatId) {
        loadChatMessages(currentChatId);
    }

    // Enviar mensagem ao assistente
    function sendMessage() {
        const message = document.getElementById('message-input').value;
        const csrftoken = getCookie('csrftoken');

        if (message.trim()) {
            addMessage(message, 'message-user');

            fetch('/api/chat_llm/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
                body: JSON.stringify({ message: message, chat_id: currentChatId })
            })
            .then(response => response.json())
            .then(data => {
                addMessage(data.response, 'message-response');

                if (!currentChatId) {
                    currentChatId = data.chat_id;
                    window.history.pushState({}, "", `/chat/${currentChatId}/`);
                }

                document.getElementById('message-input').value = '';
            })
            .catch(error => console.error('Erro:', error));
        }
    }

    // Enviar mensagem ao apertar o botão de enviar
    document.querySelector('.send-button').addEventListener('click', sendMessage);
    // Enviar mensagem ao apertar Enter
    document.getElementById('message-input').addEventListener('keypress', function (event) {
        if (event.key === 'Enter' && !event.shiftKey) {  // Evitar envio se Shift+Enter for pressionado
            event.preventDefault();  // Evitar quebra de linha ao apertar Enter
            sendMessage();  // Chamar a função de enviar
        }
    });

    function adjustTextarea() {
        const textarea = document.getElementById('message-input');
        
        // Guardar o valor do padding para considerar no cálculo da altura
        const computedStyle = window.getComputedStyle(textarea);
        const paddingTop = parseFloat(computedStyle.paddingTop);
        const paddingBottom = parseFloat(computedStyle.paddingBottom);
    
        // Resetar a altura para o mínimo, ignorando a altura atual
        textarea.style.height = 'auto';
    
        // Calcular a altura real levando em consideração o padding
        const newHeight = textarea.scrollHeight - paddingTop - paddingBottom;
    
        // Aplicar a nova altura com limite máximo de 150px
        textarea.style.height = `${Math.min(newHeight, 150)}px`;
    }
    
    // Ajustar textarea conforme o usuário digita
    document.getElementById('message-input').addEventListener('input', adjustTextarea);
})