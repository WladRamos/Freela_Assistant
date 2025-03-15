document.addEventListener("DOMContentLoaded", function () {
    let trabalhos = [];

    // Modal de edição de trabalho
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
});
