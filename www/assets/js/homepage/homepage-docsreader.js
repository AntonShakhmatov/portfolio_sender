document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('uploadForm');
    if (!form) return;
  
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
  
      try {
        const res = await fetch(form.action, {
          method: 'POST',
          body: new FormData(form),
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
          },
          credentials: 'same-origin'
        });
  
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
  
        const ct = res.headers.get('content-type') || '';
        if (!ct.includes('application/json')) {
          const text = await res.text();
          throw new Error('Non-JSON response: ' + text.slice(0, 200));
        }
  
        const data = await res.json();
  
        if (data.ok) {
          alert(data.message || 'Soubor uložen.');
          const url = data.redirect || '/homepage/create';
          window.location.assign(url);
        } else {
          alert(data.error || 'Upload failed');
        }
      } catch (err) {
        console.error(err);
        alert('Chyba při odeslání formuláře.');
      }
    });
  });
  