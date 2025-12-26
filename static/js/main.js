/**
 * Ana JavaScript dosyası
 * Form validasyonları ve UI iyileştirmeleri için kullanılır
 */

// Sayfa yüklendiğinde çalışacak fonksiyonlar
document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================
    // TC KİMLİK NUMARASI VALİDASYONU
    // ============================================
    // TC Kimlik Numarası sadece rakam girişi - Harf ve özel karakterleri engelle
    const tcInputs = document.querySelectorAll('input[name="tc_no"]');
    tcInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            // Sadece rakamları bırak, diğer karakterleri sil
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
        });
    });

    // ============================================
    // HESAP NUMARASI VALİDASYONU
    // ============================================
    // Hesap numarası sadece rakam girişi - Harf ve özel karakterleri engelle
    const hesapInputs = document.querySelectorAll('input[name="alici_hesap_no"]');
    hesapInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            // Sadece rakamları bırak, diğer karakterleri sil
            e.target.value = e.target.value.replace(/[^0-9]/g, '');
        });
    });

    // ============================================
    // TELEFON NUMARASI VALİDASYONU
    // ============================================
    // Telefon formatı - Sadece rakam ve + işaretine izin ver
    const telefonInputs = document.querySelectorAll('input[name="telefon"]');
    telefonInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            // Sadece rakam ve + işaretini bırak, diğer karakterleri sil
            e.target.value = e.target.value.replace(/[^0-9+]/g, '');
        });
    });

    // ============================================
    // FLASH MESAJLARI OTOMATİK KAPATMA
    // ============================================
    // Flash mesajları otomatik kapatma (5 saniye sonra)
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        // 5 saniye sonra mesajı kapat
        setTimeout(() => {
            // Opacity'yi 0 yaparak fade-out efekti oluştur
            message.style.opacity = '0';
            message.style.transition = 'opacity 0.3s';  // 0.3 saniyelik geçiş efekti
            // 300ms sonra mesajı DOM'dan kaldır
            setTimeout(() => message.remove(), 300);
        }, 5000);  // 5 saniye (5000ms) bekle
    });
});





