function openDetailsModalFromRow(row) {
    const modal = document.getElementById("detailsModal");
    const form = document.getElementById("editForm");
  
    // Preencher inputs
    form.elements["jobTitle"].value = row.dataset.jobTitle || "";
    form.elements["exLevel"].value = row.dataset.exLevel || "";
    form.elements["timeLimit"].value = row.dataset.timeLimit || "";
    form.elements["keyword"].value = row.dataset.keyword || "";
    form.elements["description"].value = row.dataset.description || "";
    form.elements["payment"].value = row.dataset.payment || "";
    form.elements["cost"].value = row.dataset.cost || "";
    form.elements["hourly"].value = row.dataset.hourly || "";
    form.elements["currency"].value = row.dataset.currency || "";
    form.elements["min"].value = row.dataset.min || "";
    form.elements["max"].value = row.dataset.max || "";
    form.elements["avg"].value = row.dataset.avg || "";
  
    // Preencher categorias
    const categoryContainer = document.getElementById("categoryContainer");
    categoryContainer.innerHTML = ""; // Limpar categorias anteriores
  
    for (let i = 1; i <= 9; i++) {
      const cat = row.dataset[`category${i}`];
      if (cat) {
        const span = document.createElement("span");
        span.className = "categoria";
        span.textContent = cat;
        categoryContainer.appendChild(span);
      }
    }
  
    // Resetar estado do formulário
    form.querySelectorAll("input, textarea").forEach(el => el.setAttribute("disabled", true));
    document.getElementById("saveBtn").style.display = "none";
    document.getElementById("editBtn").style.display = "inline-block";
  
    modal.style.display = "flex";

    form.setAttribute("data-id", row.dataset.id);  // Adiciona o ID do item para atualização
    form.setAttribute("data-new", "false");
  }
  
  function closeModal() {
    const modal = document.getElementById("detailsModal");
    const form = document.getElementById("editForm");
  
    // Esconder modal
    modal.style.display = "none";
  
    // Esconder campo de adicionar categoria
    document.getElementById("adicionarCategoria").style.display = "none";
    document.getElementById("novaCategoriaInput").value = "";
  
    // Remover classe 'editable' e listener das categorias antigas
    document.querySelectorAll(".categoria").forEach(cat => {
      cat.classList.remove("editable");
      const clone = cat.cloneNode(true); // remove todos os event listeners
      cat.replaceWith(clone);
    });
  
    // Resetar botões
    document.getElementById("saveBtn").style.display = "none";
    document.getElementById("editBtn").style.display = "inline-block";
  
    // Resetar campos
    form.querySelectorAll("input, textarea").forEach(el => {
      el.setAttribute("disabled", true);
    });

    form.removeAttribute("data-id");
    form.removeAttribute("data-new");
  }
  
  function enableEdit() {
    const form = document.getElementById("editForm");
    form.querySelectorAll("input, textarea").forEach(el => el.removeAttribute("disabled"));
    document.getElementById("saveBtn").style.display = "inline-block";
    document.getElementById("editBtn").style.display = "none";
  }

  function enableEdit() {
    document.querySelectorAll("#editForm input, #editForm textarea").forEach(inp => inp.removeAttribute("disabled"));
    document.getElementById("saveBtn").style.display = "inline-block";
    document.getElementById("editBtn").style.display = "none";
  
    // Habilita exclusão das categorias
    document.querySelectorAll(".categoria").forEach(cat => {
      cat.classList.add("editable");
      cat.addEventListener("click", function () {
        if (cat.classList.contains("editable")) {
          cat.remove();
        }
      });
    });
  
    // Mostra campo para adicionar nova categoria
    document.getElementById("adicionarCategoria").style.display = "block";
  }
  
  function adicionarCategoria() {
    const container = document.getElementById("categoryContainer");
    const input = document.getElementById("novaCategoriaInput");
    const valor = input.value.trim();
  
    if (valor) {
      const span = document.createElement("span");
      span.className = "categoria editable";
      span.textContent = valor;
      span.addEventListener("click", function () {
        span.remove();
      });
      container.appendChild(span);
      input.value = "";
    }
  }
  

  function openEmptyModal() {
    const modal = document.getElementById("detailsModal");
    const form = document.getElementById("editForm");
  
    // Limpa todos os campos
    form.reset();
    document.getElementById("categoryContainer").innerHTML = "";
    document.getElementById("novaCategoriaInput").value = "";
  
    // Ativa o modo de edição
    form.querySelectorAll("input, textarea").forEach(el => el.removeAttribute("disabled"));
    document.getElementById("saveBtn").style.display = "inline-block";
    document.getElementById("editBtn").style.display = "none";
    document.getElementById("adicionarCategoria").style.display = "block";
  
    // Define flag de novo item
    form.setAttribute("data-new", "true");
  
    modal.style.display = "flex";
  }
  
  // Event Listeners
  document.addEventListener("DOMContentLoaded", function () {
    const selectAll = document.getElementById("selectAll");
    const checkboxes = document.querySelectorAll(".selectCheckbox");
    const deleteBtn = document.getElementById("deleteSelectedBtn");

    deleteBtn.addEventListener("click", async function (e) {
      e.preventDefault();
    
      const confirmDelete = confirm("Tem certeza que deseja excluir os trabalhos selecionados?");
      if (!confirmDelete) return;
    
      const selectedCheckboxes = document.querySelectorAll(".selectCheckbox:checked");
      
      const ids = Array.from(selectedCheckboxes).map(cb => cb.value);
    
      const csrfToken = getCookie("csrftoken");
    
      try {
        const response = await fetch("/painel_admin/base-vetorial/deletar/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
          },
          body: JSON.stringify({ ids })
        });
    
        const result = await response.json();
    
        if (result.success) {
          alert(result.message);
          window.location.reload(); // atualiza a tabela
        } else {
          alert(result.message || "Erro ao excluir os itens.");
        }
    
      } catch (error) {
        alert("Erro ao enviar requisição de exclusão.");
        console.error(error);
      }
    });
    
  
    selectAll.addEventListener("change", function () {
      checkboxes.forEach(cb => cb.checked = selectAll.checked);
      toggleDeleteButton();
    });
  
    checkboxes.forEach(cb => {
      cb.addEventListener("change", toggleDeleteButton);
    });
  
    function toggleDeleteButton() {
      const anyChecked = Array.from(checkboxes).some(cb => cb.checked);
      deleteBtn.disabled = !anyChecked;
    }
  
    const detailButtons = document.querySelectorAll(".details-button");
    detailButtons.forEach(button => {
      button.addEventListener("click", function () {
        const row = button.closest("tr");
        openDetailsModalFromRow(row);
      });
    });
  
    document.getElementById("editBtn").addEventListener("click", enableEdit);

    document.getElementById("detailsModal").addEventListener("click", function (event) {
      if (event.target === this) {
        closeModal();
      }
    });

    document.getElementById("addBtn").addEventListener("click", openEmptyModal);

    document.getElementById("editForm").addEventListener("submit", async function (event) {
      event.preventDefault();

      const form = event.target;
      const isNew = form.getAttribute("data-new") === "true";

      const categorias = Array.from(document.querySelectorAll("#categoryContainer .categoria")).map(span => span.textContent.trim());

      const data = {
        jobTitle: form.elements["jobTitle"].value.trim(),
        exLevel: form.elements["exLevel"].value.trim(),
        timeLimit: form.elements["timeLimit"].value.trim(),
        keyword: form.elements["keyword"].value.trim(),
        description: form.elements["description"].value.trim(),
        payment: form.elements["payment"].value.trim(),
        cost: form.elements["cost"].value.trim(),
        hourly: form.elements["hourly"].value.trim(),
        currency: form.elements["currency"].value.trim(),
        min: form.elements["min"].value.trim(),
        max: form.elements["max"].value.trim(),
        avg: form.elements["avg"].value.trim(),
        categories: categorias
      };

      if (!isNew) {
        const id = form.getAttribute("data-id"); // <- agora sim, corretamente
        data.id = id;
      }

      // Validação básica para novo item
      if (isNew) {
        if (!data.jobTitle || !data.description || !(data.cost || data.hourly || data.min || data.max || data.avg)) {
          alert("Preencha o título, a descrição e pelo menos um campo de valor.");
          return;
        }
      }

      const csrfToken = getCookie("csrftoken");
      const endpoint = isNew ? "/painel_admin/base-vetorial/adicionar/" : "/painel_admin/base-vetorial/atualizar/";

      try {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
          },
          body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
          alert(result.message);
          // Redireciona para busca automática do novo título
          window.location.href = `?q=${encodeURIComponent(data.jobTitle)}`;
        } else {
          alert(result.message || "Erro ao salvar.");
        }

      } catch (error) {
        alert("Erro ao enviar dados.");
        console.error(error);
      }
    });
  });
  