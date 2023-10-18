//An event listener that waits for the HTML document to fully load and be ready for manipulation based on the ids on the html elements. 
document.addEventListener('DOMContentLoaded', () => {
    const captureButton= document.getElementById('capture-button');
    const optionsSection = document.getElementById('options');
    const takePhotoButton = document.getElementById('take-photo-button');
    const uploadPhotoButton = document.getElementById('upload-photo-button');
    const cameraContainer = document.getElementById('camera-container');
    const buttons = document.getElementById('buttons');
    const retakeButton = document.getElementById('retake-button');
    const nextButton = document.getElementById('next-button');
    const capturedPhoto = document.getElementById('captured-photo');
    const fileInput = document.getElementById('file-input');
    const canvas = capturedPhoto.getContext('2d');
    
    let isCaptured = false;
    const video = document.getElementById('camera-feed');

    // Hides the camera and display options on the web page when showing the option buttons (take/upload photo)
    function showOptions() {
        optionsSection.style.display = 'block';
        cameraContainer.style.display = 'none';
        buttons.style.display = 'none';
    }

    // Hides the options buttons and shows the camera 
    function showCamera() {
        optionsSection.style.display = 'none';
        cameraContainer.style.display = 'block';
        buttons.style.display = 'block';
    }

// Accesses the device's camera (rear-facing environment), if successful, sets the camera feed as the source as the video.
function takePhoto() {
    navigator.mediaDevices
        .getUserMedia({ video: { facingMode: 'environment' } })
        .then((stream) => {
            video.srcObject = stream;
        })
        .catch((error) => {
            console.error('Error accessing camera:', error);
        });
}

// When clicked on the take photo button, it accesses the user's camera and displays the camera on the screen.
takePhotoButton.addEventListener('click', () => {
    takePhoto();
    showCamera();
});

// This checks if a photo is not captured, it will draw the image of the video until the picture is captured, user can capture an image by pressing the capture button. 
captureButton.addEventListener('click', () => {
    if (!isCaptured) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
        capturedPhoto.style.display = 'block';
        video.style.display = 'none';

        captureButton.style.display = 'none';
        retakeButton.style.display = 'inline-block';
        nextButton.style.display = 'inline-block';

        isCaptured = true;
    }
});

// If the user clicks on the retake button, it hides the captured photo and buttons and returns to the previous camera view. 
retakeButton.addEventListener('click', () => {
    capturedPhoto.style.display = 'none';
    video.style.display = 'block';
    captureButton.style.display = 'inline-block';
    retakeButton.style.display = 'none';
    nextButton.style.display = 'none';

    isCaptured = false;
});

// Sends the image to the server using XMLHttpRequest
function sendImageToServer(imageData) {
const xhr = new XMLHttpRequest();
xhr.open('POST', '/create', true);
xhr.setRequestHeader('Content-Type', 'application/json');

xhr.onreadystatechange = () => {
    if (xhr.readyState === 4) {
        if (xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            if (response.redirect) {
                window.location.href = response.redirect;
            } else {
                console.log('Image uploaded but no redirect provided.');
            }
        } else {
            console.error('Image upload failed.');
        }
    }
};    
const data = JSON.stringify({ image: imageData });
xhr.send(data);
}

// If clicked on the next button, it will send the image to the server. 
nextButton.addEventListener('click', () => {
    if (isCaptured) {
        const imageBase64 = capturedPhoto.toDataURL('image/jpeg');
        sendImageToServer(imageBase64);
    }
});

// When clicked on the upload photo button, it asks for an input file
uploadPhotoButton.addEventListener('click', () => {
    fileInput.click();
});

// This checks if the file is an image file and converts it to base64-encoded string and sends to the server. 
fileInput.addEventListener('change', (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
        const reader = new FileReader();
        reader.onload = function () {
            const imageBase64 = reader.result;
            sendImageToServer(imageBase64);
        };
        reader.readAsDataURL(selectedFile);
    }
});
    // When the page loads, show the options first
    showOptions();
});