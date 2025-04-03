function openDetailsModalFromRow(row) {
    const fields = [
      { label: "Job Title", key: "job-title" },
      { label: "Nível de Experiência", key: "ex-level" },
      { label: "Limite de Tempo", key: "time-limit" },
      { label: "Palavra-chave", key: "keyword" },
      { label: "Descrição", key: "description" },
      { label: "Categoria 1", key: "category1" },
      { label: "Categoria 2", key: "category2" },
      { label: "Categoria 3", key: "category3" },
      { label: "Categoria 4", key: "category4" },
      { label: "Categoria 5", key: "category5" },
      { label: "Categoria 6", key: "category6" },
      { label: "Categoria 7", key: "category7" },
      { label: "Categoria 8", key: "category8" },
      { label: "Categoria 9", key: "category9" },
      { label: "Tipo de Pagamento", key: "payment" },
      { label: "Custo Total", key: "cost" },
      { label: "Valor por Hora", key: "hourly" },
      { label: "Moeda", key: "currency" },
      { label: "Preço Mínimo", key: "min" },
      { label: "Preço Máximo", key: "max" },
      { label: "Preço Médio", key: "avg" }
    ];
  
    let html = "<ul>";
    fields.forEach(f => {
      const valor = row.dataset[f.key] || "—";
      html += `<li><strong>${f.label}:</strong> ${valor}</li>`;
    });
    html += "</ul>";
  
    document.getElementById("modalContent").innerHTML = html;
    document.getElementById("detailsModal").style.display = "flex";
}
  
function closeModal() {
document.getElementById("detailsModal").style.display = "none";
}
  
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
});
