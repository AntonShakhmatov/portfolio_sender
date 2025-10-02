    // Akce po odeslání
    $(document).on('submit', '#frm-chatWindowModalForm', async (e) => {
        e.preventDefault();
    
        const form = document.getElementById('frm-chatWindowModalForm');
        const text = (form.querySelector('[name="text"]')?.value || '').trim();
        const predefined = form.querySelector('[name="predefined"]:checked')?.value || 'works';
    
        if (predefined === 'works' && !text) {
        alert('V jakem oboru si hledáš prace?');
        return;
        }
    
        // Jen pro "works" embedding, spočita se přes client
        let embedding = null;
        if (predefined === 'works') {
        try {
            embedding = await embed(text);
            console.log(embedding);
        } catch (err) {
            console.error('Embed failed:', err);
            alert('Nepodařilo se vytvořit embedding na klientu.');
            return;
        }
        }
    
        // JSON požadavek
        const resp = await fetch('/embeddings/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ predefined, text, embedding })
          });
    
        let data = null;
        try {
        data = await resp.json();
        } catch(e) {
        console.error('Bad JSON:', e);
        }
    
        // Render vysledku
        $('.chatFooter .result-block').remove();
        let html = '';
        if (data && Array.isArray(data.result) && data.result.length) {
        function renderField(label, value) {
            if (value === null || value === undefined || value === '') return '';
            return `<b>${label}:</b> ${value}<br><br>`;
        }
        data.result.forEach(function(item) {
            let htmlBlock = '<div class="result-item">';
            if (item.type === 'product') {
            htmlBlock += renderField('Name', item.name);
            htmlBlock += item.path ? `<img src="https://www83.webrex.eu/optokon/${item.path}"><br><br>` : '';
            htmlBlock += renderField('Description', item.description);
            htmlBlock += renderField('Short Description', item.short_description);
            htmlBlock += renderField('Selling price', item.selling_price);
            htmlBlock += item.url ? `<b>Odkaz:</b> <a href="https://www83.webrex.eu/optokon/product/${item.product_id}-${item.url}">${item.url}</a><br><br>` : '';
            } else if (item.type === 'markets') {
            htmlBlock += renderField('Name', item.name_branche);
            htmlBlock += renderField('Description', item.content_branche);
            } else if (item.type === 'workers') {
            htmlBlock += renderField('NameNew', item.name_new);
            htmlBlock += renderField('PerexNew', item.perex_new);
            htmlBlock += renderField('ContentNew', item.content_new);
            htmlBlock += renderField('PlaceNew', item.place_new);
            }
            htmlBlock += '</div>';
            html += htmlBlock;
        });
        } else {
        html += '<i>Nic nenašel, zkus ještě jednou:).</i>';
        }
    
        $('.chatFooter').append('<div class="result-block"><b>Výsledek:</b><br>' + html + '</div>');
        $('.chatFooter .result-block').last().css({
        'min-height': '60vh',
        'min-width': '28vw',
        'justify-self': 'center'
        });
    
        setTimeout(function() {
        $('.fa.fa-angle-double-up.doubleUp').last().css({ 'color': 'red' });
        $('.fa.fa-angle-double-down.doubleDown').last().css({ 'color': 'lawngreen' });
        }, 2500);
    });

    $(document).on('click', '.dropdown-option[data-key="markets"], .dropdown-option[data-key="workers"]', function() {
        $('input[name="predefined"]').prop('checked', false);
        $(this).find('input[name="predefined"]').prop('checked', true);
        $('#frm-chatWindowModalForm').submit();
    });

    let embedderPromise = null;

    async function getEmbedder() {
    if (!embedderPromise) {
        const tf = window.HF;
        if (!tf?.pipeline) {
        throw new Error('Transformers library is not loaded yet');
        }
        // В v3 вместо { quantized: true } используем dtype:'q8'
        embedderPromise = tf.pipeline(
        'feature-extraction',
        'Xenova/all-MiniLM-L6-v2',
        { dtype: 'q8' } // быстрый и лёгкий вариант для браузера
        );
    }
    return embedderPromise; // возвращает pipeline
    }

    async function embed(text) {
    const embedder = await getEmbedder();
    const out = await embedder(text, { pooling: 'mean', normalize: true });

    const vec =
        Array.isArray(out) ? out :
        (ArrayBuffer.isView(out?.data)) ? Array.from(out.data) :
        (ArrayBuffer.isView(out)) ? Array.from(out) :
        (() => { throw new Error('Unexpected embedding output shape'); })();

    if (vec.length !== 384) console.warn('Unexpected embedding length:', vec.length);
    return vec;
    }