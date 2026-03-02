(function () {
  const canvas = document.getElementById('canvas');
  const ctx = canvas.getContext('2d');
  const imageInput = document.getElementById('image-input');
  const uploadBtn = document.getElementById('upload-btn');
  const memeTextInput = document.getElementById('meme-text');
  const fontSizeInput = document.getElementById('font-size');
  const fontSizeValue = document.getElementById('font-size-value');
  const textBoxCount = document.getElementById('text-box-count');
  const downloadBtn = document.getElementById('download-btn');

  let templateImage = null;
  let textBoxes = [];
  let selectedIndex = null;
  let draggingIndex = null;
  let hasDragged = false;

  function getCanvasCoords(e) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY
    };
  }

  function getTextBoxBounds(tb) {
    const fontSize = Number(fontSizeInput.value);
    ctx.font = `bold ${fontSize}px "Impact", "Arial Black", sans-serif`;
    const w = tb.text ? ctx.measureText(tb.text).width : 40;
    const h = fontSize + 8;
    const pad = 4;
    return {
      left: tb.x - w / 2 - pad,
      right: tb.x + w / 2 + pad,
      top: tb.y - h / 2 - pad,
      bottom: tb.y + h / 2 + pad
    };
  }

  function getTextBoxAt(canvasX, canvasY) {
    for (let i = textBoxes.length - 1; i >= 0; i--) {
      const b = getTextBoxBounds(textBoxes[i]);
      if (canvasX >= b.left && canvasX <= b.right && canvasY >= b.top && canvasY <= b.bottom) {
        return i;
      }
    }
    return null;
  }

  function addTextBox(x, y) {
    textBoxes.push({ text: '', x, y });
    selectedIndex = textBoxes.length - 1;
    memeTextInput.value = '';
    memeTextInput.placeholder = 'Type here...';
    memeTextInput.focus();
    updateTextBoxCount();
    draw();
  }

  function selectTextBox(index) {
    selectedIndex = index;
    memeTextInput.value = textBoxes[index].text;
    memeTextInput.placeholder = 'Select a text box to edit...';
    memeTextInput.focus();
    draw();
  }

  function loadImage(file) {
    if (!file || !file.type.startsWith('image/')) return;
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = function () {
      URL.revokeObjectURL(url);
      templateImage = img;
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      textBoxes = [];
      selectedIndex = null;
      memeTextInput.value = '';
      memeTextInput.placeholder = 'Click on image to add text';
      draw();
      downloadBtn.disabled = false;
      updateTextBoxCount();
    };
    img.onerror = function () {
      URL.revokeObjectURL(url);
    };
    img.src = url;
  }

  function draw() {
    if (!templateImage) return;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.drawImage(templateImage, 0, 0);

    const fontSize = Number(fontSizeInput.value);
    fontSizeValue.textContent = fontSize;
    const lineWidth = Math.max(2, fontSize / 8);

    ctx.font = `bold ${fontSize}px "Impact", "Arial Black", sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.strokeStyle = '#000000';
    ctx.fillStyle = '#ffffff';
    ctx.lineWidth = lineWidth;

    textBoxes.forEach((tb) => {
      if (!tb.text) return;
      ctx.strokeText(tb.text, tb.x, tb.y);
      ctx.fillText(tb.text, tb.x, tb.y);
    });
  }

  function download() {
    if (!templateImage) return;
    const data = canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = data;
    a.download = 'meme.png';
    a.click();
  }

  function updateTextBoxCount() {
    const n = textBoxes.length;
    textBoxCount.textContent = n === 0 ? 'No text boxes' : n === 1 ? '1 text box' : `${n} text boxes`;
  }

  canvas.addEventListener('mousedown', function (e) {
    if (!templateImage) return;
    const coords = getCanvasCoords(e);
    const hit = getTextBoxAt(coords.x, coords.y);

    if (hit !== null) {
      draggingIndex = hit;
      hasDragged = false;
    } else {
      addTextBox(coords.x, coords.y);
    }
  });

  canvas.addEventListener('mousemove', function (e) {
    if (draggingIndex === null) return;
    hasDragged = true;
    const coords = getCanvasCoords(e);
    textBoxes[draggingIndex].x = coords.x;
    textBoxes[draggingIndex].y = coords.y;
    draw();
  });

  canvas.addEventListener('mouseup', function () {
    if (draggingIndex !== null) {
      if (!hasDragged) {
        selectTextBox(draggingIndex);
      }
      draggingIndex = null;
      hasDragged = false;
    }
  });

  canvas.addEventListener('mouseleave', function () {
    if (draggingIndex !== null) {
      draggingIndex = null;
      hasDragged = false;
    }
  });

  uploadBtn.addEventListener('click', () => imageInput.click());
  imageInput.addEventListener('change', function () {
    const file = this.files[0];
    loadImage(file);
  });

  memeTextInput.addEventListener('input', function () {
    if (selectedIndex !== null) {
      textBoxes[selectedIndex].text = this.value;
    }
    draw();
    updateTextBoxCount();
  });


  fontSizeInput.addEventListener('input', draw);
  downloadBtn.addEventListener('click', download);
  updateTextBoxCount();
})();
