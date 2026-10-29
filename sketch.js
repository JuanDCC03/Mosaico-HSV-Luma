let images = [];
let imgPaths = [];
const TOTAL_IMAGES = 60;
const SATURATION_THRESHOLD = 0.15;

// Definimos el tamaño cuadrado para cada imagen
const IMG_SIZE = 100; // Cada miniatura medirá 100px x 100px

function preload() {
  for (let i = 1; i <= TOTAL_IMAGES; i++) {
    imgPaths.push(`assets/img_${i}.jpg`);
  }

  for (let i = 0; i < imgPaths.length; i++) {
    loadImage(imgPaths[i], (img) => {
      let stats = getAverageColorStats(img);
      images.push({
        img: img,
        hue: stats.hue,
        saturation: stats.saturation,
        luma: stats.luma,
        isAchromatic: stats.saturation < SATURATION_THRESHOLD
      });

      if (images.length === TOTAL_IMAGES) {
        sortImages();
      }
    });
  }
}

function setup() {
  createCanvas(IMG_SIZE * TOTAL_IMAGES, IMG_SIZE);
  noLoop();
}

function draw() {
  background(20);

  if (images.length < TOTAL_IMAGES) return;

  for (let i = 0; i < images.length; i++) {
    let x = i * IMG_SIZE;
    drawSquareImage(images[i].img, x, 0, IMG_SIZE);
  }

  // Descarga automática de la tira cuadrada
  saveCanvas('paleta_cuadrada_ordenada', 'png');
}

function drawSquareImage(img, x, y, size) {
  let minDim = Math.min(img.width, img.height);
  let sx = (img.width - minDim) / 2;
  let sy = (img.height - minDim) / 2;

  image(img, x, y, size, size, sx, sy, minDim, minDim);
}

function getAverageColorStats(img) {
  img.loadPixels();
  let totalRed = 0, totalGreen = 0, totalBlue = 0;
  let step = 4 * 5;

  for (let i = 0; i < img.pixels.length; i += step) {
    totalRed += img.pixels[i];
    totalGreen += img.pixels[i + 1];
    totalBlue += img.pixels[i + 2];
  }

  let totalPixelSamples = img.pixels.length / step;
  let red = (totalRed / totalPixelSamples) / 255;
  let green = (totalGreen / totalPixelSamples) / 255;
  let blue = (totalBlue / totalPixelSamples) / 255;

  let luma = 0.299 * red + 0.587 * green + 0.114 * blue;

  let maxColor = Math.max(red, green, blue);
  let minColor = Math.min(red, green, blue);
  let hue, saturation;
  let lightness = (maxColor + minColor) / 2;

  if (maxColor === minColor) {
    hue = 0;
    saturation = 0;
  } else {
    let delta = maxColor - minColor;
    saturation = lightness > 0.5 ? delta / (2 - maxColor - minColor) : delta / (maxColor + minColor);
    
    switch (maxColor) {
      case red: 
        hue = (green - blue) / delta + (green < blue ? 6 : 0); 
        break;
      case green: 
        hue = (blue - red) / delta + 2; 
        break;
      case blue: 
        hue = (red - green) / delta + 4; 
        break;
    }
    hue /= 6;
  }

  return { hue: hue, saturation: saturation, luma: luma };
}