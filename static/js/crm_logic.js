$(document).ready(function() {
    // 1. Активируем поиск (Select2) для всех выпадающих списков
    $('select').select2({
        theme: 'bootstrap-5',
        width: '100%',
        placeholder: "Выберите значение",
        allowClear: true,
        language: {
            noResults: function() { return "Ничего не найдено"; }
        }
    });

    // 2. Логика авто-цены при оформлении продажи
    // Слушаем событие выбора в поле с id_vin (стандартный ID поля Django)
    $('#id_vin').on('select2:select', function (e) {
        var vin = $(this).val();
        var priceInput = $('#id_end_price'); // Поле "Итоговая цена"

        if (vin && priceInput.length > 0) {
            console.log("Запрос цены для VIN:", vin);

            // Запрос к API
            fetch(`/api/cars/${vin}`)
                .then(response => response.json())
                .then(data => {
                    let finalPrice = data.price;

                    // Считаем скидку
                    if (data.discount && data.discount > 0) {
                        finalPrice = data.price * (1 - data.discount / 100);
                    }

                    // Округляем
                    finalPrice = Math.floor(finalPrice);

                    // Вписываем в поле ввода (пользователь может потом изменить)
                    priceInput.val(finalPrice);

                    // Визуально мигаем полем, чтобы привлечь внимание
                    priceInput.css('background-color', '#ffffcc');
                    setTimeout(() => priceInput.css('background-color', ''), 500);
                })
                .catch(err => console.error("Ошибка API:", err));
        }
    });
});