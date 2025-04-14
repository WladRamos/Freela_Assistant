function normalizarNome(nome) {
  return nome
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase()
    .trim();
}

document.addEventListener("DOMContentLoaded", function () {

    // Abrir modal para adicionar novo trabalho
    document.getElementById("add-work").addEventListener("click", function () {
        limparCamposTrabalho();
        desbloquearCampos();
      
        document.getElementById("work-modal-title").innerText = "Adicionar Trabalho";
        document.getElementById("delete-work").classList.add("hidden");
        const saveBtn = document.getElementById("save-work");
        saveBtn.classList.remove("hidden");
        saveBtn.classList.add("show");
        document.getElementById("edit-work").style.display = "none";
        document.getElementById("add-skill-container").classList.remove("hidden");
        document.getElementById("work-modal").classList.remove("hidden");

        document.getElementById("work-title").focus();
      });

    // Botão de fechar modal de trabalho
    document.getElementById("close-work-modal").addEventListener("click", function () {
        limparCamposTrabalho();
        bloquearCampos();
        document.getElementById("save-work").classList.remove("show");
        document.getElementById("save-work").classList.add("hidden");
        document.getElementById("edit-work").style.display = "inline-block";
        document.getElementById("add-skill-container").classList.add("hidden");
        document.getElementById("work-modal").classList.add("hidden");
      });
  
    // Abrir modal para visualizar/editar trabalho existente
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
  
            const container = document.getElementById("work-skills");
            container.innerHTML = "";
  
            data.habilidades.forEach(hab => {
              const tag = document.createElement("span");
              tag.className = "skill-tag";
              tag.dataset.id = hab.id;
              tag.innerHTML = `${hab.nome} <span class="remove-skill">x</span>`;
              container.appendChild(tag);
            });
  
            bloquearCampos();
            const saveBtn = document.getElementById("save-work");
            saveBtn.classList.add("hidden");
            saveBtn.classList.remove("show");
            document.getElementById("edit-work").style.display = "inline-block";
            document.getElementById("delete-work").classList.remove("hidden");
            document.getElementById("add-skill-container").classList.add("hidden");
  
            document.getElementById("work-modal").classList.remove("hidden");
          });
      });
    });
  
    // Editar trabalho existente
    document.getElementById("edit-work").addEventListener("click", function () {
        desbloquearCampos();
        
        document.getElementById("work-title").focus();
      
        // Exibir botões e input de nova habilidade
        const saveBtn = document.getElementById("save-work");
        const editBtn = document.getElementById("edit-work");
        const addSkillContainer = document.getElementById("add-skill-container");
      
        if (saveBtn && editBtn && addSkillContainer) {
          saveBtn.classList.remove("hidden");
          saveBtn.classList.add("show");
          editBtn.style.display = "none";
          addSkillContainer.classList.remove("hidden");
      
          // Ativar edição nas tags
          document.querySelectorAll("#work-skills .skill-tag").forEach(tag => {
            tag.classList.add("editable");
          });
        } else {
          console.warn("Elemento(s) não encontrado(s):", { saveBtn, editBtn, addSkillContainer });
        }
      });
  
    // Salvar trabalho
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
  
    // Excluir trabalho
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
  
    // Adicionar nova habilidade
    document.getElementById("add-work-skill").addEventListener("click", function () {
      const input = document.getElementById("new-work-skill");
      const rawSkill = input.value;
      const newSkill = normalizarNome(rawSkill);
    
      if (!newSkill) return;
    
      // Verifica se já foi adicionada ao trabalho
      const jaAdicionada = Array.from(document.querySelectorAll("#work-skills .skill-tag")).some(tag => {
        const nomeTag = normalizarNome(tag.textContent.replace(" x", ""));
        return nomeTag === newSkill;
      });
    
      if (jaAdicionada) {
        alert("Essa habilidade já foi adicionada ao trabalho.");
        return;
      }
    
      // Cria tag visual
      const tag = document.createElement("span");
      tag.className = "skill-tag editable";
      tag.innerHTML = `${newSkill} <span class="remove-skill">x</span>`;
      document.getElementById("work-skills").appendChild(tag);
      input.value = "";
    });
  
    // Remover habilidade ao clicar no "x"
    document.addEventListener("click", function (event) {
      if (event.target.classList.contains("remove-skill")) {
        event.target.parentElement.remove();
      }
    });
  
    // Salvar preferências de preço
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
  
    // Abrir modal de adicionar habilidade ao perfil
    document.getElementById("add-skill").addEventListener("click", function () {
      input = document.getElementById("new-skill")
      input.value = "";
      document.getElementById("skill-modal").classList.remove("hidden");
      input.focus();
    });
  
    // Adicionar habilidade ao perfil
    document.getElementById("save-skill").addEventListener("click", function () {
      let skillName = document.getElementById("new-skill").value.trim().toUpperCase();
      if (!skillName) return;
  
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
            if (!data.nova) {
              alert("Essa habilidade já está no seu perfil.");
              return;
            }
            const skillsContainer = document.querySelector(".profile-box.skills .skills");
            let noSkillsMessage = skillsContainer.querySelector("p");
            if (noSkillsMessage) noSkillsMessage.remove();

            const tag = document.createElement("span");
            tag.className = "skill-tag perfil";
            tag.dataset.id = data.habilidade_id;
            tag.innerHTML = `${skillName} <span class="remove-skill">x</span>`;

            // Adiciona a nova skill antes do botão, se ele existir
            const addSkillButton = skillsContainer.querySelector("#add-skill");
            if (addSkillButton) {
            skillsContainer.insertBefore(tag, addSkillButton);
            } else {
            skillsContainer.appendChild(tag);
            }
            document.getElementById("skill-modal").classList.add("hidden");
          } else {
            alert("Erro ao adicionar habilidade: " + data.error);
          }
        })
        .catch(error => console.error("Erro ao adicionar habilidade:", error));
    });
  
    // Remover habilidade do perfil
    document.addEventListener("click", function (event) {
      if (event.target.classList.contains("remove-skill")) {
        const tag = event.target.parentElement;
        const skillId = tag.dataset.id;
  
        fetch(`/remover_habilidade/${skillId}/`, {
          method: "DELETE",
          headers: {
            "X-CSRFToken": getCookie("csrftoken")
          }
        })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              tag.remove();
              if (document.querySelectorAll(".skills .skill-tag").length === 0) {
                const p = document.createElement("p");
                p.textContent = "Nenhuma habilidade cadastrada.";
                document.querySelector(".skills").insertBefore(p, document.getElementById("add-skill"));
              }
            } else {
              alert("Erro ao remover habilidade: " + data.error);
            }
          })
          .catch(error => console.error("Erro ao remover habilidade:", error));
      }
    });
  
    // Fechar modais
    document.querySelectorAll(".close").forEach(btn => {
      btn.addEventListener("click", function () {
        this.closest(".modal").classList.add("hidden");
      });
    });

    // Botão "Fechar" do modal de habilidade
    document.getElementById("close-skill-modal").addEventListener("click", function () {
        document.getElementById("skill-modal").classList.add("hidden");
    });
  
    // Funções utilitárias
    function limparCamposTrabalho() {
      document.getElementById("work-id").value = "";
      document.getElementById("work-title").value = "";
      document.getElementById("work-description").value = "";
      document.getElementById("work-payment").value = "Hora";
      document.getElementById("work-value").value = "";
      document.getElementById("work-skills").innerHTML = "";
      document.getElementById("new-work-skill").value = "";
    }
  
    function bloquearCampos() {
      ["work-title", "work-description", "work-payment", "work-value"].forEach(id => {
        document.getElementById(id).setAttribute("disabled", true);
      });
      document.querySelectorAll("#work-skills .skill-tag").forEach(tag => {
        tag.classList.remove("editable");
      });
    }
  
    function desbloquearCampos() {
      ["work-title", "work-description", "work-payment", "work-value"].forEach(id => {
        document.getElementById(id).removeAttribute("disabled");
      });
    }

    document.querySelectorAll(".modal").forEach(modal => {
        modal.addEventListener("click", function (event) {
          // Se clicou diretamente no fundo do modal (e não dentro do conteúdo)
          if (event.target === modal) {
            modal.classList.add("hidden");
      
            // Extra: se for o modal de trabalho, também limpa e bloqueia
            if (modal.id === "work-modal") {
              limparCamposTrabalho();
              bloquearCampos();
      
              const saveBtn = document.getElementById("save-work");
              saveBtn.classList.remove("show");
              saveBtn.classList.add("hidden");
      
              document.getElementById("edit-work").style.display = "inline-block";
              document.getElementById("add-skill-container").classList.add("hidden");
            }
          }
        });
      });
  
  });
  