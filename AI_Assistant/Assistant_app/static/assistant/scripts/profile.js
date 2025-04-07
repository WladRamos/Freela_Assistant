document.addEventListener("DOMContentLoaded", function () {

    // Abrir modal para adicionar novo trabalho
    document.getElementById("add-work").addEventListener("click", function () {
      limparCamposTrabalho();
      desbloquearCampos();
      document.getElementById("work-modal-title").innerText = "Adicionar Trabalho";
      document.getElementById("delete-work").classList.add("hidden");
      document.getElementById("save-work").style.display = "inline-block";
      document.getElementById("edit-work").style.display = "none";
      document.getElementById("add-skill-container").classList.remove("hidden");
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
            document.getElementById("save-work").style.display = "none";
            document.getElementById("edit-work").style.display = "inline-block";
            document.getElementById("delete-work").classList.remove("hidden");
            document.getElementById("add-skill-container").classList.add("hidden");
  
            document.getElementById("work-modal").classList.remove("hidden");
          });
      });
    });
  
    // Ativar edição
    document.getElementById("edit-work").addEventListener("click", function () {
      desbloquearCampos();
      document.getElementById("save-work").style.display = "inline-block";
      document.getElementById("edit-work").style.display = "none";
      document.getElementById("add-skill-container").classList.remove("hidden");
    });
  
    // Fechar modal
    document.querySelectorAll(".close").forEach(closeBtn => {
      closeBtn.addEventListener("click", function () {
        fecharModal();
      });
    });
  
    // Salvar ou editar trabalho
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
  
    // Adicionar nova habilidade no modal
    document.getElementById("add-work-skill").addEventListener("click", adicionarSkill);
  
    // Remover habilidade no modal
    document.addEventListener("click", function (event) {
      if (event.target.classList.contains("remove-skill")) {
        event.target.parentElement.remove();
      }
    });
  
    // Salvar preços
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
  
    // Salvar nova habilidade no banco
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
              const skillsContainer = document.querySelector(".skills");
              const addSkillButton = document.getElementById("add-skill");
  
              let noSkillsMessage = document.querySelector(".skills p");
              if (noSkillsMessage) {
                noSkillsMessage.remove();
              }
  
              const skillTag = document.createElement("span");
              skillTag.className = "skill-tag";
              skillTag.dataset.id = data.habilidade_id;
              skillTag.innerHTML = `${skillName} <span class="remove-skill">x</span>`;
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
  
    // Remover habilidade do perfil
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
  });
  
  // Funções auxiliares
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
  }
  
  function desbloquearCampos() {
    ["work-title", "work-description", "work-payment", "work-value"].forEach(id => {
      document.getElementById(id).removeAttribute("disabled");
    });
  }
  
  function fecharModal() {
    document.getElementById("work-modal").classList.add("hidden");
  }
  
  function adicionarSkill() {
    const input = document.getElementById("new-work-skill");
    const valor = input.value.trim().toUpperCase();
    if (valor) {
      const tag = document.createElement("span");
      tag.className = "skill-tag";
      tag.innerHTML = `${valor} <span class="remove-skill">x</span>`;
      document.getElementById("work-skills").appendChild(tag);
      input.value = "";
    }
  }
  