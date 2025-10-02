$(function () {
    function closeChatOnOutsideClick(event) {
        if (!$(event.target).closest(".chatWindow, .chatButton").length) {
            manageChatWindowAction();
        }
    }

    function manageChatWindowAction() {
        $(".chatModal").toggle();

        if ($(".chatModal").is(":visible")) {
            $(".chatBody").scrollTop($(".chatBody")[0].scrollHeight);
            $('#frm-chatWindowModalForm .chatFooter .messageInput').focus();
            document.addEventListener("click", closeChatOnOutsideClick, false);
        } else {
            document.removeEventListener("click", closeChatOnOutsideClick, false);
        }
    }

    $(document).ajaxComplete(function( event, request, settings ) {
        $(".chatBody").scrollTop($(".chatBody")[0].scrollHeight);
    });

    $(".chatButton").on("click", function() {
        manageChatWindowAction();
    });

    $(".closeChat").on("click", function() {
        manageChatWindowAction();
    });

    let typeTextTimeout = null;

    function typeText(element, text, speed = 35, cb = null) {
        if (typeTextTimeout) clearTimeout(typeTextTimeout);
    
        let i = 0;
        element.textContent = '';
    
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                typeTextTimeout = setTimeout(type, speed);
            } else if (cb) {
                cb();
            }
        }
        type();
    }            
    
    $(function() {
        const helloText = 'Ahoj, jak bych ti mohl pomoct?';
        typeText(document.getElementById('assistant-hello'), helloText, 35);
    });

    $(document).on('click', function (e) {
        if (!$(e.target).closest('.predefined-dropdown').length) {
            $('.predefined-dropdown').removeClass('open');
        }
    });
    
    $(function () {
        $('.dropdown-selected').on('click', function () {
            $(this).closest('.predefined-dropdown').toggleClass('open');
        });
    
        $('.dropdown-option').on('click', function () {
            let key = $(this).data('key');
            let iconHtml = $(this).find('i').prop('outerHTML');
            let labelText = $(this).find('span.icon-option > span').text();
    
            $(this).find('input[type=radio]').prop('checked', true).trigger('change');
    
            let selected = $(this).closest('.predefined-dropdown').find('.selected-icon');
            selected.html(iconHtml + '<span>' + labelText + '</span>');

            $(this).closest('.predefined-dropdown').removeClass('open');
        });

        $(document).on('click', '.dropdown-option[data-key="contacts"], .dropdown-option[data-key="works"]', function() {
            $('input[name="predefined"]').prop('checked', false);
            $(this).find('input[name="predefined"]').prop('checked', true);
            $('input.form-control.me-2').hide();
            $('button.sendButton.ladda-button').hide();
        });  
        
        $(document).on('click', '.dropdown-option[data-key="works"]', function() {
            $('input[name="predefined"]').prop('checked', false);
            $(this).find('input[name="predefined"]').prop('checked', true);
            $('input.form-control.me-2').show();
            $('button.sendButton.ladda-button').show();
        });

        $(document).on('click', ' .dropdown-option[data-key="works"]', function() {
            const helloText = 'Jaky obor plánuješ vybrat?';
            typeText(document.getElementById('assistant-hello'), helloText, 35);
        });

        $(document).on('click', ' .dropdown-option[data-key="workers"]', function() {
            const helloText = 'Tady jsou všechny pracovní nabídky.';
            typeText(document.getElementById('assistant-hello'), helloText, 35);
        });

        $(document).on('click', ' .dropdown-option[data-key="markets"]', function() {
            const helloText = 'Tady jsou všechny kontakty.';
            typeText(document.getElementById('assistant-hello'), helloText, 35);
        });

        $(document).on('click', 'button.sendButton.ladda-button', function() {
            const helloText = 'Hledám něco podle tvého požadavku...';
            typeText(document.getElementById('assistant-hello'), helloText, 35);
        });
        
        function hideFormLater() {
            setTimeout(function() {
                $('#frm-chatWindowModalForm').hide();
            }, 2500);
        }
        
        $(document).on('click', '.dropdown-option[data-key="workers"], .dropdown-option[data-key="markets"]', function() {
            $('input[name="predefined"]').prop('checked', false);
            $(this).find('input[name="predefined"]').prop('checked', true);
            hideFormLater();
            $('.result-block').addClass('result-block--large');
        });
        
        $(document).on('click', 'button.sendButton.ladda-button', function() {
            hideFormLater();
            $('.result-block').addClass('result-block--large');
        });    
        
        $(document).on('click', 'button > i.fa.fa-angle-double-up.doubleUp', function() {
            $('#frm-chatWindowModalForm').hide();
            $(this).css('color', 'red');
            $('button > i.fa.fa-angle-double-down.doubleDown').last().css('color', 'lawngreen');
        });
        
        $(document).on('click', 'button > i.fa.fa-angle-double-down.doubleDown', function() {
            $('#frm-chatWindowModalForm').show();
            $(this).css('color', 'red');
            $('button > i.fa.fa-angle-double-up.doubleUp').last().css('color', 'lawngreen');
        });
    });
    
    $(document).on('submit', '#frm-chatWindowModalForm', function(e){
        e.preventDefault();
    
        let text = $(this).find('input[name="text"]').val();
        let predefined = $(this).find('input[name="predefined"]:checked').val();
        $.ajax({
            url: '/embeddings/control',
            method: 'GET',
            data: { 
                text: text,
                predefined: predefined
            },
            dataType: 'json',
            success: function(data){
                $('.chatFooter .result-block').remove();
                let html = '';
                if (Array.isArray(data.result) && data.result.length) {
                    function renderField(label,value){
                        if(value === null || value === undefined || value === '') return '';
                        return `<b>${label}:</b> ${value}<br><br>`;
                    }
                    data.result.forEach(function(item) {
                        let htmlBlock = '<div class="result-item">';
                        if (item.type === 'works') {
                            //htmlBlock += renderField('ID', item.product_id);
                            htmlBlock += renderField('Name', item.name);
                            htmlBlock += item.path ? `<img src="https://www83.webrex.eu/optokon/${item.path}"><br><br>` : '';
                            htmlBlock += renderField('Description', item.description);
                            htmlBlock += renderField('Short Description', item.short_description);
                            htmlBlock += renderField('Selling price', item.selling_price);
                            htmlBlock += item.url ? `<b>Odkaz:</b> <a href="https://www83.webrex.eu/optokon/product/${item.product_id}-${item.url}">${item.url}</a><br><br>` : '';
                            //htmlBlock += renderField('Similarita', item.similarity !== undefined ? item.similarity.toFixed(3) : null);
                        } else if (item.type === 'markets') {
                            //htmlBlock += renderField('ID', item.article_id);
                            htmlBlock += renderField('Name', item.name_branche);
                            htmlBlock += renderField('Description', item.content_branche);
                            //htmlBlock += renderField('Similarita', (typeof item.similarity === 'number') ? item.similarity.toFixed(3) : null);
                        } else if (item.type === 'workers') {
                            //htmlBlock += renderField('ID', item.article_id);
                            htmlBlock += renderField('NameNew', item.name_new);
                            htmlBlock += renderField('PerexNew', item.perex_new);
                            htmlBlock += renderField('ContentNew', item.content_new);
                            htmlBlock += renderField('PlaceNew', item.place_new);
                            //htmlBlock += renderField('Similarita', (typeof item.similarity === 'number') ? item.similarity.toFixed(3) : null);
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
                $('.fa.fa-angle-double-up.doubleUp').last().css({
                    'color': 'red'
                })
                },2500);

                setTimeout(function() {
                    $('.fa.fa-angle-double-down.doubleDown').last().css({
                        'color': 'lawngreen'
                    })
                },2500);

                $(document).on('click', 'button > i.fa.fa-angle-double-down.doubleDown', function() {
                    let clickedIcon = $(this);
                    setTimeout(function() {
                        $('#frm-chatWindowModalForm').show();
                        clickedIcon.css({
                            'color': 'red'
                        });
                        $('.fa.fa-angle-double-up.doubleUp').last().css({
                            'color': 'lawngreen'
                        });
                    });
                });                                         
            }  
        });
    }); 
    $(document).on('click', '.dropdown-option[data-key="markets"], .dropdown-option[data-key="workers"]', function() {
        $('input[name="predefined"]').prop('checked', false);
        $(this).find('input[name="predefined"]').prop('checked', true);
        $('#frm-chatWindowModalForm').submit();
    });                              
});