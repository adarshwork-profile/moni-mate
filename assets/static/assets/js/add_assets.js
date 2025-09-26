
// toggles between fields depending on the asset type.

document.addEventListener('DOMContentLoaded', function() {
    const typeField = document.querySelector('select[name="type"]');
    const quantityField = document.querySelector('input[name="quantity"]');

    function toggleQuantityFields() {
        if (typeField.value === 'gold') {
            quantityField.closest('p').style.display = 'block';
        } else if (typeField.value === 'silver') {
            quantityField.closest('p').style.display = 'block';
        } else {
            quantityField.closest('p').style.display = 'none';
        }
    }

    typeField.addEventListener('change', toggleQuantityFields);
    toggleQuantityFields(); // Initialize on page load
});
