document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const recipientCheckboxes = document.querySelectorAll('.recipient-checkbox');

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            recipientCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }

    setTimeout(function () {
        let alerts = document.querySelectorAll('.alert');
        alerts.forEach(function (alert) {
            let bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 1500);

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            const inputs = registerForm.querySelectorAll('input, textarea');
            let allFieldsFilled = true;

            for (let i = 0; i < inputs.length; i++) {
                if (inputs[i].type !== 'hidden' && inputs[i].value.trim() === '') {
                    allFieldsFilled = false;
                    break;
                }
            }

            if (!allFieldsFilled) {
                event.preventDefault();
                alert('Please fill out all fields.');
            }
        });
    }
});