// static/js/1.js
document.addEventListener('DOMContentLoaded', function() {
    // Player search functionality
    const playerSearch = document.getElementById('playerSearch');
    if (playerSearch) {
        playerSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const cards = document.querySelectorAll('.player-card');
            
            cards.forEach(card => {
                const playerName = card.querySelector('.card-title').textContent.toLowerCase();
                card.parentElement.style.display = playerName.includes(searchTerm) ? 'block' : 'none';
            });
        });
    }

    // Handle transfer bids
document.querySelectorAll('.transfer-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
        const playerId = e.target.dataset.playerId;
        const response = await fetch(`/transfer/${playerId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        if (result.success) {
            e.target.textContent = 'Bid Sent!';
            e.target.disabled = true;
        }
    });
});
    
    // Add to team button handler
    const addButtons = document.querySelectorAll('.btn-outline-primary');
    addButtons.forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.player-card');
            const playerName = card.querySelector('.card-title').textContent;
            alert(`Added ${playerName} to your team!`);
            // In a real app, you would make an AJAX call here
        });
    });
});