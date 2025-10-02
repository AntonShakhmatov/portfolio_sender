// document.addEventListener('DOMContentLoaded', () => {
//     if (document.getElementById('uploadSuccess')) {
//         alert('Priveeet! Файл загружен.');
//         $(document).ready(function(){
//             ReadFile();
//         });
//         function ReadFile(){
//             jQuery.ajax({
//                 type: "POST",
//                 url: 'PdfTextExtractor.php',
//                 data: {}, 
//                  success:function(data) {
//                 alert(data); 
//                  }
//             });
//         }
//         // return;
//     }      
//   });

// www/assets/js/upload-form.js
document.addEventListener('DOMContentLoaded', () => {
    // если был успешный аплоад (после редиректа)
    if (document.getElementById('uploadSuccess')) {
      // вызовем Presenter → сервис → получим JSON
      fetch(window.EXTRACT_URL, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' } // чтобы это считалось AJAX
      })
        .then(r => r.json())
        .then(data => {
          if (data.ok) {
            alert('Priveeet! Текст извлечён.');
            console.log(data.text); // делай с текстом что нужно
          } else {
            alert('Ошибка: ' + (data.error || 'unknown'));
          }
        })
        .catch(err => alert('Network error: ' + err));
    }
  });
  
  