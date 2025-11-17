(async () => {
  const video = document.getElementById('video');
  const canvas = document.getElementById('snapshot');
  const ctx = canvas.getContext('2d');
  const result = document.getElementById('result');
  const stream = await navigator.mediaDevices.getUserMedia({video:true});
  video.srcObject = stream;
  setInterval(async ()=>{
    ctx.drawImage(video,0,0,canvas.width,canvas.height);
    const img = canvas.toDataURL('image/jpeg');
    const res = await fetch('/recognize', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({image: img})
    });
    
    if (!res.ok) {
      if (res.status === 401) {
        result.innerText = 'Session expired. Please login again.';
        setTimeout(() => window.location.href = '/login', 2000);
        return;
      }
      result.innerText = 'Error occurred';
      return;
    }
    
    const json = await res.json();
    if (json.error) {
      result.innerText = `Error: ${json.error}`;
    } else {
      result.innerText = json.recognized.length? json.recognized.join(', '): 'No face';
    }
  },2000);
})();