document.addEventListener('DOMContentLoaded', function() {
    const typeField = document.querySelector('select[name="type"]');
    const creditLimitField = document.querySelector('input[name="credit_limit"]');
    const spentPercentField = document.querySelector('input[name="spent_percent"]');
    const balanceField = document.querySelector('input[name="balance"]');
    const minimumBalanceField = document.querySelector('input[name="minimum_balance"]');
    const accountTypeField = document.querySelector('input[name="account_type"]');

    function toggleCreditCardFields() {
        if (typeField.value === 'credit_card') {
            balanceField.closest('p').style.display = 'none';
            minimumBalanceField.closest('p').style.display = 'none';
            accountTypeField.closest('p').style.display = 'none';
            creditLimitField.closest('p').style.display = 'block';
            spentPercentField.closest('p').style.display = 'block';
        } else if (typeField.value === 'cash') {
            minimumBalanceField.closest('p').style.display = 'none';
            accountTypeField.closest('p').style.display = 'none';
        } else {
            creditLimitField.closest('p').style.display = 'none';
            spentPercentField.closest('p').style.display = 'none';
            balanceField.closest('p').style.display = 'block';
            minimumBalanceField.closest('p').style.display = 'block';
            accountTypeField.closest('p').style.display = 'block';
        }
    }

    typeField.addEventListener('change', toggleCreditCardFields);
    toggleCreditCardFields(); // Initialize on page load
});
