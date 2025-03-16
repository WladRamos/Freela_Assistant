document.addEventListener("DOMContentLoaded", function () {
    // Abrir modal para adicionar novo trabalho
    document.getElementById("add-work").addEventListener("click", function () {
        limparCamposTrabalho();
        document.getElementById("work-modal-title").innerText = "Adicionar Trabalho";
        document.getElementById("delete-work").classList.add("hidden"); // Oculta o botão de excluir
        document.getElementById("work-modal").classList.remove("hidden");
    });

    // Abrir modal para editar trabalho existente
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

                    // Preencher habilidades do trabalho
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
                    document.getElementById("delete-work").classList.remove("hidden"); // Exibe o botão de excluir
                    document.getElementById("work-modal").classList.remove("hidden");
                })
                .catch(error => console.error("Erro ao buscar trabalho:", error));
        });
    });

    // Salvar ou editar trabalho no banco ao confirmar no modal
    document.getElementById("save-work").addEventListener("click", function () {
        let work = {
            id: document.getElementById("work-id").value,
            titulo: document.getElementById("work-title").value,
            descricao: document.getElementById("work-description").value,
            tipo_pagamento: document.getElementById("work-payment").value,
            valor_pagamento: document.getElementById("work-value").value,
            habilidades: Array.from(document.querySelectorAll("#work-skills .skill-tag")).map(skill => ({
                id: skill.dataset.id || null,
                nome: skill.textContent.replace(" x", "").trim()
            }))
        };

        fetch("/salvar_trabalho/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify(work)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Trabalho salvo com sucesso!");
                location.reload();
            } else {
                alert("Erro ao salvar trabalho: " + data.error);
            }
        })
        .catch(error => console.error("Erro ao salvar trabalho:", error));
    });

    // Excluir trabalho ao clicar no botão de excluir
    document.getElementById("delete-work").addEventListener("click", function () {
        const workId = document.getElementById("work-id").value;
        if (!workId) return;

        fetch(`/excluir_trabalho/${workId}/`, {
            method: "DELETE",
            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Trabalho excluído com sucesso!");
                location.reload();
            } else {
                alert("Erro ao excluir trabalho: " + data.error);
            }
        })
        .catch(error => console.error("Erro ao excluir trabalho:", error));
    });

    // Adicionar nova habilidade ao modal do trabalho
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

    // Remover habilidades do modal de trabalho ao clicar no "x"
    document.addEventListener("click", function (event) {
        if (event.target.classList.contains("remove-skill")) {
            event.target.parentElement.remove();
        }
    });

    // Salvar preferências de preços ao clicar no botão
    document.getElementById("save-prices").addEventListener("click", function () {
        let formData = {
            preco_fixo_min: document.querySelector("[name='preco_fixo_min']").value,
            preco_hora_min: document.querySelector("[name='preco_hora_min']").value
        };

        fetch("/salvar_precos/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Preços atualizados!");
            } else {
                alert("Erro ao atualizar preços: " + data.error);
            }
        })
        .catch(error => console.error("Erro ao atualizar preços:", error));
    });

    // Adicionar nova habilidade ao perfil
    document.getElementById("add-skill").addEventListener("click", function () {
        document.getElementById("new-skill").value = "";
        document.getElementById("skill-modal").classList.remove("hidden");
    });

    // Salvar nova habilidade no banco ao confirmar no modal
    document.getElementById("save-skill").addEventListener("click", function () {
        let skillName = document.getElementById("new-skill").value.trim().toUpperCase();
        
        if (skillName) {
            fetch("/adicionar_habilidade/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify({ nome: skillName })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const skillTag = document.createElement("span");
                    skillTag.className = "skill-tag";
                    skillTag.dataset.id = data.habilidade_id;
                    skillTag.innerHTML = `${skillName} <span class="remove-skill">x</span>`;

                    const skillsContainer = document.querySelector(".skills");
                    const addSkillButton = document.getElementById("add-skill");
                    skillsContainer.insertBefore(skillTag, addSkillButton);

                    document.getElementById("new-skill").value = "";
                    document.getElementById("skill-modal").classList.add("hidden");
                } else {
                    alert("Erro ao adicionar habilidade: " + data.error);
                }
            })
            .catch(error => console.error("Erro ao adicionar habilidade:", error));
        }
    });

     // ** Remover habilidade ao clicar no "x" **
     document.addEventListener("click", function (event) {
        if (event.target.classList.contains("remove-skill")) {
            const skillElement = event.target.parentElement;
            const skillId = skillElement.dataset.id;

            fetch(`/remover_habilidade/${skillId}/`, {
                method: "DELETE",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken")
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    skillElement.remove();

                    // Se não houver mais habilidades, exibir a mensagem "Nenhuma habilidade cadastrada"
                    let remainingSkills = document.querySelectorAll(".skills .skill-tag").length;
                    if (remainingSkills === 0) {
                        const skillsContainer = document.querySelector(".skills");
                        let noSkillsMessage = document.createElement("p");
                        noSkillsMessage.textContent = "Nenhuma habilidade cadastrada.";
                        skillsContainer.insertBefore(noSkillsMessage, document.getElementById("add-skill"));
                    }
                } else {
                    alert("Erro ao remover habilidade: " + data.error);
                }
            })
            .catch(error => console.error("Erro ao remover habilidade:", error));
        }
    });

    // Fechar os modais ao clicar no botão "X"
    document.querySelectorAll(".close").forEach(closeBtn => {
        closeBtn.addEventListener("click", function () {
            this.parentElement.parentElement.classList.add("hidden");
        });
    });

    // Função para limpar campos do modal de trabalho
    function limparCamposTrabalho() {
        document.getElementById("work-id").value = "";
        document.getElementById("work-title").value = "";
        document.getElementById("work-description").value = "";
        document.getElementById("work-payment").value = "Hora";
        document.getElementById("work-value").value = "";
        document.getElementById("work-skills").innerHTML = "";
    }
});
