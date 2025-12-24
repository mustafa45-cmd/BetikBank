// TC Kimlik Numarası sadece rakam girişi
document.addEventListener('DOMContentLoaded', function() {
    const tcInputs = document.querySelectorAll('input[name="tc_no"]');
    tcInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
        });
    });

    // Hesap numarası sadece rakam girişi
    const hesapInputs = document.querySelectorAll('input[name="alici_hesap_no"]');
    hesapInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
        });
    });

    // Telefon formatı
    const telefonInputs = document.querySelectorAll('input[name="telefon"]');
    telefonInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/[^0-9+]/g, '');
        });
    });

    // Flash mesajları otomatik kapatma (5 saniye)
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transition = 'opacity 0.3s';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
});


