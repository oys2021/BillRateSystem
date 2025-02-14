document.getElementById('submitBtn').addEventListener('click', function () {
    // Get all input and select elements within the form
    const form = document.getElementById('myForm');
    const inputs = form.querySelectorAll('input, select');
    let allValid = true; // Flag to track if all fields are valid

    inputs.forEach(input => {
        const value = input.value.trim();
        
        if (!value) {
            allValid = false;
            input.style.border = '1px solid red';
            input.focus();
            alert(`${input.previousElementSibling.innerText || 'Field'} is required.`);
            return; 
        } else {
            // Remove highlighting if the field becomes valid
            input.style.border = '';
        }
    });

    // If all fields are valid, validate email and submit the form
    if (allValid) {
        const emailInput = document.getElementById('emailInput').value;
        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

        if (!emailPattern.test(emailInput)) {
            alert('Please enter a valid email address.');
            return; 
        }

        // If everything is valid, submit the form
        form.submit();
    }
});
