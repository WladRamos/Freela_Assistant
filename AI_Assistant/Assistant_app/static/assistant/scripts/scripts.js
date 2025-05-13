function scrollToBottomSmooth() {
    const messageArea = document.getElementById("message-area");
    messageArea.scrollTo({
        top: messageArea.scrollHeight,
        behavior: "smooth"
    });
}

function aplicarTargetBlankNosLinks(container) {
    const links = container.querySelectorAll("a");
    links.forEach(link => {
        link.setAttribute("target", "_blank");
        link.setAttribute("rel", "noopener noreferrer");
    });
}

// Função para carregar os chats na barra lateral
function loadChatList() {
    fetch('/api/chats/')
        .then(response => response.json())
        .then(data => {
            const chatList = document.getElementById("chat-list");
            chatList.innerHTML = ""; // Limpa a lista antes de recarregar

            const novaConversa = document.createElement("li");
            novaConversa.classList.add("chat-item");
            novaConversa.textContent = "Iniciar nova conversa";
            novaConversa.style.fontWeight = "bold";
            novaConversa.style.cursor = "pointer";
            novaConversa.addEventListener("click", function () {
                window.location.href = "/";
            });

            chatList.appendChild(novaConversa);

            data.chats.forEach(chat => {
                let li = document.createElement("li");
                li.classList.add("chat-item");

                let chatName = document.createElement("span");
                chatName.textContent = chat.nome;
                chatName.classList.add("chat-name");
                chatName.addEventListener("click", function () {
                    window.location.href = `/chat/${chat.id}/`;
                });

                let menuButton = document.createElement("button");
                menuButton.textContent = "⋮";
                menuButton.classList.add("chat-menu-button");
                menuButton.addEventListener("click", function (event) {
                    event.stopPropagation();
                    toggleChatMenu(chat.id);
                });

                let dropdownMenu = document.createElement("div");
                dropdownMenu.classList.add("chat-menu");
                dropdownMenu.setAttribute("id", `menu-${chat.id}`);
                dropdownMenu.innerHTML = `
                    <button onclick="renameChat(${chat.id})">Renomear</button>
                    <button onclick="deleteChat(${chat.id})">Excluir</button>
                `;

                li.appendChild(chatName);
                li.appendChild(menuButton);
                li.appendChild(dropdownMenu);
                chatList.appendChild(li);
            });
        })
        .catch(error => console.error("Erro ao carregar conversas:", error));
}

// Função para alternar o menu de opções de um chat
function toggleChatMenu(chatId) {
    document.querySelectorAll(".chat-menu").forEach(menu => {
        let parentLi = menu.closest(".chat-item"); // Encontra o <li> pai do menu

        if (menu.id !== `menu-${chatId}`) {
            menu.classList.remove("active");
            parentLi.classList.remove("active"); // Remove a classe do <li>
        }
    });

    let menu = document.getElementById(`menu-${chatId}`);
    let parentLi = menu.closest(".chat-item");

    menu.classList.toggle("active");
    parentLi.classList.toggle("active"); // Adiciona a classe ao <li> ativo
}

// Função para renomear um chat
function renameChat(chatId) {
    let newName = prompt("Digite o novo nome para o chat:");
    if (newName) {
        fetch(`/api/chat/${chatId}/rename/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ nome: newName }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadChatList();
            } else {
                alert("Erro ao renomear chat.");
            }
        });
    }
}

// Função para excluir um chat
function deleteChat(chatId) {
    if (confirm("Tem certeza que deseja excluir esta conversa?")) {
        fetch(`/api/chat/${chatId}/delete/`, {
            method: "DELETE",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadChatList();
                // Verifica se o usuário está atualmente na página do chat excluído
                let pathParts = window.location.pathname.replace(/\/$/, "").split("/");
                let currentChatId = pathParts.length > 2 && pathParts[1] === "chat" ? pathParts[2] : null;

                if (currentChatId == chatId) {
                    window.location.href = "/"; // Apenas redireciona se o usuário estava na página do chat excluído
                }
            } else {
                alert("Erro ao excluir chat.");
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function(){
    let pathParts = window.location.pathname.replace(/\/$/, "").split("/");
    let currentChatId = pathParts.length > 2 && pathParts[1] === "chat" ? pathParts[2] : null;

    // Função para adicionar uma mensagem ao chat
    function addMessage(content, className) {
        const messageArea = document.getElementById('message-area');
        const messageBox = document.createElement('div');
        messageBox.classList.add('message-box', className);
        messageBox.innerHTML = DOMPurify.sanitize(marked.parse(content));
        aplicarTargetBlankNosLinks(messageBox);
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
                // Foca no input após carregar o chat
                const input = document.getElementById("message-input");
                if (input && !input.disabled) {
                    input.focus();
                }
            })
            .catch(error => console.error("Erro ao carregar mensagens:", error));
    }

    // Função para fechar o dropdown quando clicar fora
    document.addEventListener("click", function (event) {
        document.querySelectorAll(".chat-menu").forEach(menu => {
            if (!menu.contains(event.target) && !menu.previousElementSibling.contains(event.target)) {
                menu.classList.remove("active");
            }
        });
    });

    // Chamar a função ao carregar a página
    loadChatList();

    // Mostrar mensagem de boas-vindas se estiver na página inicial e nenhuma conversa estiver ativa
    if (!currentChatId) {
        const welcomeMessage = document.getElementById("welcome-message");

        // Define saudação de acordo com a hora local
        function getGreeting() {
            const hour = new Date().getHours();
            if (hour < 12) return "Bom dia";
            if (hour < 18) return "Boa tarde";
            return "Boa noite";
        }

        // Substitui apenas o início da mensagem
        const currentText = welcomeMessage.innerHTML;
        const updatedText = currentText.trim().replace(/^Bom dia/, getGreeting());

        welcomeMessage.innerHTML = updatedText;
        welcomeMessage.style.display = "block";
    }

    // Se estiver em um chat específico, carregar mensagens
    if (currentChatId) {
        loadChatMessages(currentChatId);
    }

    const input = document.getElementById("message-input");
    if (input && !input.disabled) {
        input.focus();
    }

    function sendMessage() {
        const input = document.getElementById('message-input');
        const sendButton = document.querySelector('.send-button');
        const message = input.value;
        const csrftoken = getCookie('csrftoken');
        const messageArea = document.getElementById("message-area");
    
        if (message.trim()) {
            addMessage(message, 'message-user');
            
            const welcomeMessage = document.getElementById("welcome-message");
            if (welcomeMessage) {
                welcomeMessage.style.display = "none";
            }
    
            input.value = "";
            input.disabled = true;
            sendButton.disabled = true;
    
            // Cria a caixinha de resposta já com a animação de digitação
            const responseBox = document.createElement("div");
            responseBox.classList.add("message-box", "message-response", "typing-indicator");
            responseBox.innerHTML = `<span></span><span></span><span></span>`;
            messageArea.appendChild(responseBox);
            messageArea.scrollTop = messageArea.scrollHeight;
    
            // Prepara renderização com streaming-markdown
            const renderer = smd.default_renderer(responseBox);
            const parser = smd.parser(renderer);
            let buffer = "";
            let lastWasList = false;
            let respostaIniciada = false;
    
            fetch('/api/chat_llm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
                body: JSON.stringify({ message: message, chat_id: currentChatId })
            }).then(async response => {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
    
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) {
                        input.disabled = false;
                        sendButton.disabled = false;
                        input.focus();
    
                        if (!currentChatId && response.headers.get("X-Chat-Id")) {
                            currentChatId = response.headers.get("X-Chat-Id");
                            window.history.pushState({}, "", `/chat/${currentChatId}/`);
                            loadChatList();
                        }
    
                        smd.parser_end(parser);
                        aplicarTargetBlankNosLinks(responseBox);
                        break;
                    }
    
                    if (value) {
                        buffer += decoder.decode(value);
                        const lines = buffer.split("\n");
    
                        for (let i = 0; i < lines.length - 1; i++) {
                            const line = lines[i].trim();
                            if (line.startsWith("data:")) {
                                const chunk = line.replace("data:", "").trim();
                                if (chunk !== "") {
                                    // Quando a primeira parte da resposta chegar, remove o indicador
                                    if (!respostaIniciada) {
                                        responseBox.classList.remove("typing-indicator");
                                        responseBox.innerHTML = "";
                                        respostaIniciada = true;
                                    }
    
                                    const isListItem = /^[-*+] /.test(chunk) || /^\d+\./.test(chunk);
                                    const isHeading = chunk.startsWith("#");
                                    const isNormalParagraph = !isListItem && !isHeading;
    
                                    if (lastWasList && isNormalParagraph) {
                                        smd.parser_write(parser, "\n\n");
                                    }
                                    
                                    if (isHeading) {
                                        smd.parser_write(parser, "\n\n");
                                        smd.parser_write(parser, chunk + "\n\n");
                                    } else {
                                        smd.parser_write(parser, chunk + "\n");
                                    }
                                    
                                    // Aplica efeito de fade-in ao último elemento renderizado (independente do tipo)
                                    setTimeout(() => {
                                        const lastChild = responseBox.lastElementChild;
                                        if (lastChild && !lastChild.classList.contains('fade-in-chunk')) {
                                            lastChild.classList.add('fade-in-chunk');
                                        }
                                    }, 10);
    
                                    lastWasList = isListItem;
                                    //scrollToBottomSmooth();
                                }
                            }
                        }
    
                        buffer = lines[lines.length - 1];
                    }
                }
            }).catch(error => {
                console.error("Erro no streaming:", error);
                input.disabled = false;
                sendButton.disabled = false;
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