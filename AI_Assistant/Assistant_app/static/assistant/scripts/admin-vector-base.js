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
  }
  
  function closeModal() {
    document.getElementById("detailsModal").style.display = "none";
  }
  
  function enableEdit() {
    const form = document.getElementById("editForm");
    form.querySelectorAll("input, textarea").forEach(el => el.removeAttribute("disabled"));
    document.getElementById("saveBtn").style.display = "inline-block";
    document.getElementById("editBtn").style.display = "none";
  }
  
  // Event Listeners
  document.addEventListener("DOMContentLoaded", function () {
    const selectAll = document.getElementById("selectAll");
    const checkboxes = document.querySelectorAll(".selectCheckbox");
    const deleteBtn = document.getElementById("deleteSelectedBtn");
  
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
  });
  