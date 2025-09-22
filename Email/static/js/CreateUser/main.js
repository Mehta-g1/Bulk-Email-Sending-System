document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
        let alerts = document.querySelectorAll('.alert1');
        alerts.forEach(function (alert) {
            let bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 2000);

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function (event) {
            const inputs = registerForm.querySelectorAll('input, textarea, ');
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




//  Form chaker
document.querySelector("form").addEventListener("submit", function (e) {
    let current = document.getElementById("current_password").value.trim();
    let newPass = document.getElementById("new_password").value.trim();
    let confirmPass = document.getElementById("confirm_password").value.trim();

    // 1️⃣ Empty field check
    if (!current || !newPass || !confirmPass) {
        alert("All fields are required.");
        e.preventDefault();
        return;
    }

    // 2️⃣ New password validation
    // At least 8 chars, 1 uppercase, 1 lowercase, 1 digit
    let passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,}$/;
    if (!passwordRegex.test(newPass)) {
        alert("New password must be at least 6 characters long and include uppercase, lowercase, and a number.");
        e.preventDefault();
        return;
    }

    // 3️⃣ Confirm password check
    if (newPass !== confirmPass) {
        alert("New password and confirm password do not match.");
        e.preventDefault();
        return;
    }
});



document.getElementById("selectAll").addEventListener("change", function (e) {
    let checkboxes = document.querySelectorAll(".recipient-checkbox");
    checkboxes.forEach(cb => cb.checked = e.target.checked);
});


