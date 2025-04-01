function openBanModal(userId, username) {
    document.getElementById('BanUserId').value = userId;
    document.getElementById('BanUserInfo').textContent = `Usuário: ${username}`;
    document.getElementById('BanModal').style.display = 'block';
}

function openSuspendModal(userId, username) {
document.getElementById('suspendUserId').value = userId;
document.getElementById('suspendUserInfo').textContent = `Usuário: ${username}`;
document.getElementById('suspendModal').style.display = 'block';
}

function closeModal() {
document.getElementById('BanModal').style.display = 'none';
document.getElementById('suspendModal').style.display = 'none';
}