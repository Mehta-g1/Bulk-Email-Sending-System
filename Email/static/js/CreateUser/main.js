const form = document.getElementById("registerForm");
const submitBtn = document.getElementById("submitBtn");

const loginPassword = document.getElementById("loginPassword");
const loginConfirmPassword = document.getElementById("loginConfirmPassword");
const loginStrength = document.getElementById("loginStrength");
const loginMatch = document.getElementById("loginMatch");

const emailPassword = document.getElementById("emailPassword");
const emailConfirmPassword = document.getElementById("emailConfirmPassword");
const emailMatch = document.getElementById("emailMatch");

const Name = document.getElementById("name");
const email = document.getElementById("email");

// ✅ Password Strength Checker
function checkPasswordStrength(password) {
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?#&_])[A-Za-z\d@$!%*?#&_]{6,}$/;
    return regex.test(password);
}

function validateForm() {
    let valid = true;

    // Login Password strength
    if (!checkPasswordStrength(loginPassword.value)) {
        loginStrength.textContent = "Password must be min 6 chars with upper, lower, number & special char.";
        valid = false;
    } else {
        loginStrength.textContent = "";
    }

    // Login Password match
    if (loginPassword.value !== loginConfirmPassword.value || loginConfirmPassword.value === "") {
        loginMatch.textContent = "Passwords do not match.";
        valid = false;
    } else {
        loginMatch.textContent = "";
    }

    // Email Password match
    if (emailPassword.value !== emailConfirmPassword.value || emailConfirmPassword.value === "") {
        emailMatch.textContent = "Email passwords do not match.";
        valid = false;
    } else {
        emailMatch.textContent = "";
    }

    // Other fields
    if (Name.value.trim() === "" || email.value.trim() === "") {
        valid = false;
    }

    // Enable/Disable Submit
    submitBtn.disabled = !valid;
    return valid;
}

// Events
form.addEventListener("input", validateForm);

form.addEventListener("submit", function (e) {
    if (!validateForm()) {
        e.preventDefault();
        alert("Please fill all fields correctly before submitting!");
    }
});


setTimeout(function () {
    let alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        let bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    });
}, 3000);