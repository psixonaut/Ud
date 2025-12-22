$(document).ready(function() {
    $('select').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: "Выберите значение",
        allowClear: true,
        language: {
            noResults: function() { return "Ничего не найдено"; }
        }
    });

    $('#id_vin').on('select2:select', function (e) {
        var vin = $(this).val();
        var priceInput = $('#id_end_price');
        if (vin && priceInput.length > 0) {
            console.log("Запрос цены для VIN:", vin);
            fetch(`/api/cars/${vin}`)
                .then(response => response.json())
                .then(data => {
                    let finalPrice = data.price;
                    if (data.discount && data.discount > 0) {
                        finalPrice = data.price * (1 - data.discount / 100);
                    }
                    finalPrice = Math.floor(finalPrice);
                    priceInput.val(finalPrice);
                    priceInput.css('background-color', '#ffffcc');
                    setTimeout(() => priceInput.css('background-color', ''), 500);
                })
                .catch(err => console.error("Ошибка API:", err));
        }
    });
});