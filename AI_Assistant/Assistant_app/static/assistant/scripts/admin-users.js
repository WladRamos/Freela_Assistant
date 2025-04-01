function openBanModal(userId, username) {
    document.getElementById('BanUserId').value = userId;
    document.getElementById('BanUserInfo').textContent = `Usuário: ${username}`;
    document.getElementById('BanModal').style.display = 'flex';
}

function openSuspendModal(userId, username) {
document.getElementById('suspendUserId').value = userId;
document.getElementById('suspendUserInfo').textContent = `Usuário: ${username}`;
document.getElementById('suspendModal').style.display = 'flex';
}

function closeModal() {
document.getElementById('BanModal').style.display = 'none';
document.getElementById('suspendModal').style.display = 'none';
}

function toggleDropdown(button) {
    // Fecha todos os dropdowns abertos
    document.querySelectorAll('.dropdown').forEach(drop => {
      if (drop !== button.parentElement) {
        drop.classList.remove('active');
      }
    });
  
    // Alterna o dropdown clicado
    const dropdown = button.parentElement;
    dropdown.classList.toggle('active');
  }
  
  // Fecha dropdowns ao clicar fora
  document.addEventListener('click', function (event) {
    const isDropdownButton = event.target.matches('.dropdown button');
    const isInsideDropdown = event.target.closest('.dropdown');
  
    if (!isDropdownButton && !isInsideDropdown) {
      document.querySelectorAll('.dropdown').forEach(drop => drop.classList.remove('active'));
    }
  });