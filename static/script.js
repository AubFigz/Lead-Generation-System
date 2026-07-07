document.addEventListener('DOMContentLoaded', () => {
    // Confirm delete action
    const deleteButtons = document.querySelectorAll('.delete-lead');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function () {
            const leadId = this.dataset.id;
            if (confirm('Are you sure you want to delete this lead?')) {
                fetch(`/api/leads/${leadId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    if (response.ok) {
                        alert('Lead deleted successfully');
                        location.reload();
                    } else {
                        alert('Error deleting lead');
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        });
    });

    // Display success message for actions
    const successMessage = document.getElementById('success-message');
    if (successMessage) {
        setTimeout(() => {
            successMessage.style.display = 'none';
        }, 3000); // Hide after 3 seconds
    }
});
