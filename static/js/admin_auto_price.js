document.addEventListener('DOMContentLoaded', function() {
    console.log("Auto Price Script Loaded 🚀");

    function updatePrice(selectElement) {
        const vin = selectElement.value;
        if (!vin) return;

        // 1. Ищем поле цены внутри строки с машиной (Inline)
        const container = selectElement.closest('.inline-related');
        const inlinePriceInput = container ? container.querySelector('input[name$="-discounted_prise"]') : null;

        // 2. Ищем ГЛАВНОЕ поле цены продажи (End Price)
        const mainPriceInput = document.querySelector('#id_end_price');

        // Запрос к API
        fetch(`/api/cars/${vin}`)
            .then(response => {
                if (!response.ok) throw new Error('Car not found');
                return response.json();
            })
            .then(data => {
                let finalPrice = data.price;

                // Считаем скидку
                if (data.discount && data.discount > 0) {
                    finalPrice = data.price * (1 - data.discount / 100);
                }

                finalPrice = Math.floor(finalPrice);

                // Заполняем поле в строке машины (если нашли)
                if (inlinePriceInput) {
                    inlinePriceInput.value = finalPrice;
                    flashInput(inlinePriceInput);
                }

                // Заполняем ГЛАВНОЕ поле (если оно пустое или 0)
                if (mainPriceInput && (mainPriceInput.value == 0 || mainPriceInput.value == '')) {
                    mainPriceInput.value = finalPrice;
                    flashInput(mainPriceInput);
                }
            })
            .catch(error => console.error('Error:', error));
    }

    function flashInput(element) {
        element.style.transition = "background-color 0.3s";
        element.style.backgroundColor = "#ffffcc";
        setTimeout(() => element.style.backgroundColor = "white", 500);
    }

    document.body.addEventListener('change', function(e) {
        if (e.target.matches('select[name$="-vin"]')) {
            updatePrice(e.target);
        }
    });
});