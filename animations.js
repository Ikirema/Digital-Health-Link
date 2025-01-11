const canvas = document.getElementById('animationCanvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

// Load images
const mosquitoImage = new Image();
mosquitoImage.src = 'mosquito.jpg'; 

const tabletImage = new Image();
tabletImage.src = 'tablet.jpg'; 

const netImage = new Image();
netImage.src = 'net.jpg'; 

// Create multiple mosquitoes
const mosquitoes = Array.from({ length: 50 }, () => ({
  x: Math.random() * canvas.width,
  y: Math.random() * canvas.height,
  width: 30,
  height: 30,
  speedX: Math.random() * 4 - 2, // Random speed between -2 and 2
  speedY: Math.random() * 4 - 2,
  alive: true,
}));

// Create multiple tablets
const tablets = Array.from({ length: 10}, (_, i) => ({
  x: Math.random() * canvas.width,
  y: canvas.height - 80, // Positioned near the bottom
  width: 100,
  height: 40,
}));

// Create multiple nets
const nets = Array.from({ length: 3 }, (_, i) => ({
  x: Math.random() * canvas.width,
  y: Math.random() * (canvas.height / 2), // Positioned near the middle
  width: 200,
  height: 50,
}));

// Draw objects
function drawMosquito(mosquito) {
  if (mosquito.alive) {
    ctx.drawImage(mosquitoImage, mosquito.x, mosquito.y, mosquito.width, mosquito.height);
  }
}

function drawTablet(tablet) {
  ctx.drawImage(tabletImage, tablet.x, tablet.y, tablet.width, tablet.height);
}

function drawNet(net) {
  ctx.drawImage(netImage, net.x, net.y, net.width, net.height);
}

// Check collision between two objects
function checkCollision(obj1, obj2) {
  return (
    obj1.x < obj2.x + obj2.width &&
    obj1.x + obj1.width > obj2.x &&
    obj1.y < obj2.y + obj2.height &&
    obj1.y + obj1.height > obj2.y
  );
}

// Update mosquito position and check collisions
function updateMosquito(mosquito) {
  if (!mosquito.alive) return;

  mosquito.x += mosquito.speedX;
  mosquito.y += mosquito.speedY;

  // Bounce off edges
  if (mosquito.x < 0 || mosquito.x + mosquito.width > canvas.width) mosquito.speedX *= -1;
  if (mosquito.y < 0 || mosquito.y + mosquito.height > canvas.height) mosquito.speedY *= -1;

  // Check collisions with tablets and nets
  for (const tablet of tablets) {
    if (checkCollision(mosquito, tablet)) {
      mosquito.alive = false;
      break;
    }
  }

  for (const net of nets) {
    if (checkCollision(mosquito, net)) {
      mosquito.alive = false;
      break;
    }
  }

  // If mosquito "dies", make it fall
  if (!mosquito.alive) {
    mosquito.speedX = 0;
    mosquito.speedY = 5; // Falls down
  }
}

// Animation loop
function animate() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw and update mosquitoes
  for (const mosquito of mosquitoes) {
    drawMosquito(mosquito);
    updateMosquito(mosquito);
  }

  // Draw tablets and nets
  for (const tablet of tablets) {
    drawTablet(tablet);
  }

  for (const net of nets) {
    drawNet(net);
  }

  requestAnimationFrame(animate);
}

// Handle canvas resize
window.addEventListener('resize', () => {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
});

// Start the animation
animate();
