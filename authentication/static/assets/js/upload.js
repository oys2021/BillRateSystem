let fileInput = document.getElementById("upload");
let button = document.getElementById("uploadid");
let progress = document.querySelector("progress");
let p_i = document.querySelector(".progress-indicator");
let buttons = document.querySelectorAll("button");
let load = 0;
let process = null;
let uploadedFileName = null; 
let uploadedSheetName = null;  


fileInput.oninput = () => {
    let file = fileInput.files[0];

    if (!file) return;

    let filename = file.name;
    let extension = filename.split(".").pop().toLowerCase();
    let filesize = file.size;

    // Validate file type
    if (!["csv"].includes(extension)) {
        Swal.fire({
            icon: "error",
            title: "Invalid File Type",
            text: "Only CSV files are allowed!",
            confirmButtonColor: "#d33",
        }).then(() => {
            fileInput.value = "";
            fileInput.dispatchEvent(new Event('change'));
        });
        return;
    }

    filesize = filesize < 1000000 ? (filesize / 1000).toFixed(2) + " KB" :
               filesize < 1000000000 ? (filesize / 1000000).toFixed(2) + " MB" :
               (filesize / 1000000000).toFixed(2) + " GB";

    // Display file details
    document.querySelector("label").innerText = filename;
    document.querySelector(".ex").innerText = extension.toUpperCase();
    document.querySelector(".size").innerText = filesize;

    button.disabled = false;
};

function uploadFile(file) {
    let formData = new FormData();
    formData.append("file", file);

    Swal.fire({
        title: 'Uploading...',
        text: 'Please wait while the file is being uploaded...',
        allowOutsideClick: false,
        onBeforeOpen: () => {
            Swal.showLoading();
        }
    });

    fetch('/upload_temp_file/', { 
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        Swal.close();

        if (data.error) {
            Swal.fire({
                icon: 'error',
                title: 'Upload Error',
                text: data.error,
            }).then(() => {
                fileInput.value = "";
                fileInput.dispatchEvent(new Event('change'));
            });
        } else {
            uploadedFileName = data.file_name; 
            startUploadProgress();
        }
    })
    .catch(error => {
        Swal.close();
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Network Error',
            text: 'There was a problem connecting to the server.',
        });
    });
}

function startUploadProgress() {
    document.querySelector(".pr").style.display = "block";
    load = 0;
    progress.value = 0;
    p_i.innerText = "";

    if (buttons.length >= 1) {
        buttons[0].onclick = (e) => {
            e.preventDefault();
            if (buttons.length >= 2) {
                buttons[1].style.visibility = "visible";
            }
            buttons[0].classList.add("active");

            process = setInterval(() => {
                if (load >= 100) {
                    clearInterval(process);
                    
                    p_i.innerHTML = "✅ Upload Complete"; 

                    buttons[0].classList.remove("active");

                    confirmProcessing(); 
                } else {
                    load++;
                    progress.value = load;
                    p_i.innerHTML = load + "% Uploading...";
                }
            }, 50);
        };
    }
}

function confirmProcessing() {
    if (!uploadedFileName) return;

    Swal.fire({
        title: 'Processing File...',
        text: 'Validating and processing uploaded file...',
        allowOutsideClick: false,
        onBeforeOpen: () => {
            Swal.showLoading();
        }
    });

    fetch("/process_file/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
       body: JSON.stringify({ file_name: uploadedFileName})
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            Swal.fire({
                icon: 'error',
                title: 'Processing Error',
                text: data.error
            });
        } else {
            uploadedSheetName = data.sheet_name;
            Swal.fire({
                icon: 'success',
                title: 'Success',
                text: ` ${uploadedFileName} uploaded successfully!${uploadedSheetName}`,
                confirmButtonText: 'View Invoice'
            }).then(() => {
                window.location.href = data.redirect_url; 
            });
        }
    })
    .catch(error => console.error("Error:", error));    
}


fileInput.addEventListener('change', function() {
    let file = fileInput.files[0];

    if (file) {
        button.disabled = false;
        uploadFile(file); 
    }
});
