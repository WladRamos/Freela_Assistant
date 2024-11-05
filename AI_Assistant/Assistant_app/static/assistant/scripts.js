document.addEventListener('DOMContentLoaded', function(){
    // Função para adicionar uma mensagem à área de mensagens
    function addMessage(content, className) {
        const messageArea = document.getElementById('message-area');
        const messageBox = document.createElement('div');
        messageBox.classList.add('message-box', className);
        messageBox.textContent = content;
        messageArea.appendChild(messageBox);

        // Rolar para o final da área de mensagens
        setTimeout(() => {
            messageArea.scrollTop = messageArea.scrollHeight;
        }, 0);
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Função para enviar mensagem com fetch
    function sendMessage() {
        const message = document.getElementById('message-input').value;
        const csrftoken = getCookie('csrftoken'); // Obter o token CSRF

        if (message.trim()) {
            // Exibe a mensagem do usuário na área de diálogo
            addMessage(message, 'message-user');

            fetch('/api/chat_llm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,  // Adicionar o token CSRF no cabeçalho
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                // Exibe a resposta do servidor na área de diálogo
                addMessage(data.response, 'message-response');
                
                // Limpar campo de texto e resetar altura
                document.getElementById('message-input').value = '';
                document.getElementById('message-input').style.height = '50px';
            })
            .catch(error => {
                console.error('Erro:', error);
            });
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