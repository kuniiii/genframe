let eventSource = new EventSource('/stream');
let img1, img2;
let blend = 0;
let increment = 0.01;
let url1 = '/latest.png', url2 = '/latest.png?2';
let isLoading = false;
let lastImageUrl = '';

eventSource.onmessage = function(event) {
    // This function is called whenever the server sends an update
    let data = event.data;
    if (data !== 'no file') {
        let latest_png = data;  // the server sends the filename of the new image
        url2 = '/latest.png?' + latest_png + '&' + new Date().getTime();

        // Load the new image if the previous image has finished loading
        if (!isLoading && url2 !== lastImageUrl) {
            isLoading = true;  // Set isLoading to true before starting to load the image
            img2 = loadImage(url2, img => loadImageCallback(img, url2));
        }
    }
};



async function loadImageCallback(img, url) {
    if (!img.loaded || img.width === 0) {  // Check if the image has finished loading
        console.error("Failed to load image: " + url);
        if (url !== lastImageUrl) {
            await delay(2000);  // Only delay if we're loading a new image
            isLoading = true;  // Set isLoading to true before starting to load the image
            img2 = loadImage(url, img => loadImageCallback(img, url));
        }
    } else {
        console.log("loaded something");
        isLoading = false;  // The image has loaded successfully
    }
    lastImageUrl = url;
}


function setup() {
    let canvas = createCanvas(windowWidth, windowHeight);
    canvas.parent('image-container');  // This is to attach the canvas to your image-container div

    // Load initial images
    isLoading = true; // Set isLoading to true before starting to load the images
    img1 = loadImage(url1, img => loadImageCallback(img, url1));
    img2 = loadImage(url2, img => loadImageCallback(img, url2));
}

function draw() {
    background(0);
    // Blend the images
    blendMode(BLEND);
    tint(255, 255*(1-blend));
    image(img1, 0, 0, windowWidth, windowHeight);
    tint(255, 255*blend);
    image(img2, 0, 0, windowWidth, windowHeight);

    // Increase blend amount
    blend += increment;
    if (blend > 1) {
        // Reset blend amount and swap images
        blend = 0;
        img1 = img2;

        // The next image will be loaded in the onmessage function when the server sends an update
    }
}

// A function that returns a Promise that resolves after a set amount of time
function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}