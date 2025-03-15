document.addEventListener("DOMContentLoaded", function () {
    let trabalhos = [];
    let habilidades = new Set();

    // Função para abrir o modal para adicionar um novo trabalho
    document.getElementById("add-work").addEventListener("click", function () {
        document.getElementById("work-id").value = "";
        document.getElementById("work-title").value = "";
        document.getElementById("work-description").value = "";
        document.getElementById("work-payment").value = "Hora";
        document.getElementById("work-value").value = "";
        document.getElementById("work-skills").innerHTML = "";

        document.getElementById("work-modal-title").innerText = "Adicionar Trabalho";
        document.getElementById("work-modal").classList.remove("hidden");
    });

    // Modal de edição de trabalho existente
    document.querySelectorAll(".work-title").forEach(item => {
        item.addEventListener("click", function () {
            const workId = this.dataset.id;

            fetch(`/get_trabalho/${workId}/`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById("work-id").value = data.id;
                    document.getElementById("work-title").value = data.titulo;
                    document.getElementById("work-description").value = data.descricao;
                    document.getElementById("work-payment").value = data.tipo_pagamento;
                    document.getElementById("work-value").value = data.valor_pagamento;

                    const habilidadesContainer = document.getElementById("work-skills");
                    habilidadesContainer.innerHTML = "";

                    data.habilidades.forEach(habilidade => {
                        const skillTag = document.createElement("span");
                        skillTag.className = "skill-tag";
                        skillTag.dataset.id = habilidade.id;
                        skillTag.innerHTML = `${habilidade.nome} <span class="remove-skill">x</span>`;
                        habilidadesContainer.appendChild(skillTag);
                    });

                    document.getElementById("work-modal-title").innerText = "Editar Trabalho";
                    document.getElementById("work-modal").classList.remove("hidden");
                })
                .catch(error => console.error("Erro ao buscar trabalho:", error));
        });
    });

    document.addEventListener("click", function (event) {
        if (event.target.classList.contains("remove-skill")) {
            event.target.parentElement.remove();
        }
    });

    document.getElementById("add-work-skill").addEventListener("click", function () {
        const newSkill = document.getElementById("new-work-skill").value.trim().toUpperCase();
        if (newSkill) {
            const skillTag = document.createElement("span");
            skillTag.className = "skill-tag";
            skillTag.innerHTML = `${newSkill} <span class="remove-skill">x</span>`;
            document.getElementById("work-skills").appendChild(skillTag);
            document.getElementById("new-work-skill").value = "";
        }
    });

    document.getElementById("save-work").addEventListener("click", function () {
        let work = {
            id: document.getElementById("work-id").value,
            titulo: document.getElementById("work-title").value,
            descricao: document.getElementById("work-description").value,
            tipo_pagamento: document.getElementById("work-payment").value,
            valor_pagamento: document.getElementById("work-value").value,
            habilidades: Array.from(document.querySelectorAll("#work-skills .skill-tag")).map(skill => skill.textContent.replace(" x", ""))
        };

        trabalhos.push(work);
        document.getElementById("work-modal").classList.add("hidden");
    });

    document.querySelectorAll(".close").forEach(closeBtn => {
        closeBtn.addEventListener("click", function () {
            this.parentElement.parentElement.classList.add("hidden");
        });
    });

    // Função para abrir o modal de adicionar habilidades
    document.getElementById("add-skill").addEventListener("click", function () {
        document.getElementById("new-skill").value = "";
        document.getElementById("skill-modal").classList.remove("hidden");
    });

    // Fechar os modais ao clicar no botão de fechar (X)
    document.querySelectorAll(".close").forEach(closeBtn => {
        closeBtn.addEventListener("click", function () {
            this.parentElement.parentElement.classList.add("hidden");
        });
    });

    // Função para adicionar nova habilidade ao front-end
    document.getElementById("save-skill").addEventListener("click", function () {
        let skillName = document.getElementById("new-skill").value.trim().toUpperCase();
        
        if (skillName) {
            // Criar um novo elemento para a habilidade
            const skillTag = document.createElement("span");
            skillTag.className = "skill-tag";
            skillTag.innerHTML = `${skillName} <span class="remove-skill">x</span>`;
    
            // Inserir a nova skill ANTES do botão "+"
            const skillsContainer = document.querySelector(".skills");
            const addSkillButton = document.getElementById("add-skill");
            skillsContainer.insertBefore(skillTag, addSkillButton);
    
            // Limpar o campo de entrada e fechar o modal
            document.getElementById("new-skill").value = "";
            document.getElementById("skill-modal").classList.add("hidden");
        }
    });

    // Remover habilidades da interface ao clicar no "x"
    document.addEventListener("click", function (event) {
        if (event.target.classList.contains("remove-skill")) {
            event.target.parentElement.remove();
        }
    });
});
