
function validatePasswords(e) {
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm_password").value;

    const strongRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?#&])[A-Za-z\d@$!%*?#&]{6,}$/;

    if (!strongRegex.test(password)) {
        alert("Password is too weak. Please use at least 6 characters with upper, lower, digit, special char.");
        return false;
    }

    if (password !== confirmPassword) {
        alert("Passwords do not match!");
        e.preventDefault()
        return false;
    }
    return true;
}


document.querySelector('.resetLink').addEventListener('click',(e)=>{
    validatePasswords(e)
})




