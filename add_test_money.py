"""
Test için mevcut kullanıcıların hesaplarına para ekleme scripti
Bu script, geliştirme ve test amaçlı olarak tüm kullanıcıların vadesiz hesaplarına para ekler.
"""
# Gerekli modelleri ve uygulamayı import et
from app import app, db, User, Hesap

def add_test_money(amount=10000.0):
    """
    Tüm kullanıcıların vadesiz hesaplarına para ekler
    
    Args:
        amount (float): Eklenecek para miktarı (varsayılan: 10000.0 TL)
    """
    # Uygulama bağlamı içinde çalış (veritabanı işlemleri için gerekli)
    with app.app_context():
        # Tüm kullanıcıları veritabanından al
        users = User.query.all()
        
        # Kullanıcı kontrolü - Hiç kullanıcı yoksa işlemi durdur
        if not users:
            print("Hiç kullanıcı bulunamadı!")
            return
        
        # İşlem bilgilerini yazdır
        print(f"Toplam {len(users)} kullanıcı bulundu.")
        print(f"Her kullanıcıya {amount:.2f} TL ekleniyor...\n")
        
        updated_count = 0  # Güncellenen kullanıcı sayacı
        
        # Her kullanıcı için işlem yap
        for user in users:
            # Her kullanıcının vadesiz hesaplarını bul
            vadesiz_hesaplar = Hesap.query.filter_by(
                kullanici_id=user.id,
                hesap_turu='Vadesiz'
            ).all()
            
            if vadesiz_hesaplar:
                # Vadesiz hesap varsa - İlk vadesiz hesaba para ekle
                hesap = vadesiz_hesaplar[0]  # İlk vadesiz hesabı al
                eski_bakiye = hesap.bakiye  # Eski bakiyeyi kaydet
                hesap.bakiye += amount  # Bakiyeye para ekle
                
                db.session.commit()  # Değişiklikleri kaydet
                
                # İşlem sonucunu yazdır
                print(f"[OK] {user.ad} {user.soyad} ({user.tc_no})")
                print(f"  Hesap: {hesap.hesap_no}")
                print(f"  Eski bakiye: {eski_bakiye:.2f} TL -> Yeni bakiye: {hesap.bakiye:.2f} TL\n")
                updated_count += 1  # Sayaç artır
            else:
                # Vadesiz hesap yoksa - Yeni vadesiz hesap oluştur
                hesap_no = f"{user.tc_no}{user.id:05d}"[:16]  # Hesap numarası oluştur
                yeni_hesap = Hesap(
                    hesap_no=hesap_no,
                    kullanici_id=user.id,
                    bakiye=amount,  # Başlangıç bakiyesi olarak eklenen tutar
                    hesap_turu='Vadesiz'
                )
                db.session.add(yeni_hesap)  # Yeni hesabı veritabanına ekle
                db.session.commit()  # Değişiklikleri kaydet
                
                # İşlem sonucunu yazdır
                print(f"[OK] {user.ad} {user.soyad} ({user.tc_no}) - YENI HESAP OLUSTURULDU")
                print(f"  Hesap: {yeni_hesap.hesap_no}")
                print(f"  Bakiye: {amount:.2f} TL\n")
                updated_count += 1  # Sayaç artır
        
        # İşlem özetini yazdır
        print(f"\n[Tamamlandi] Islem tamamlandi! {updated_count} kullaniciya para eklendi.")

# Script doğrudan çalıştırılıyorsa
if __name__ == '__main__':
    import sys  # Komut satırı argümanları için
    
    # Komut satırından miktar al (varsayılan 10.000 TL)
    amount = 10000.0  # Varsayılan miktar
    if len(sys.argv) > 1:  # Komut satırından miktar verilmişse
        try:
            amount = float(sys.argv[1])  # Argümanı float'a çevir
        except ValueError:
            # Geçersiz değer hatası
            print("Geçersiz miktar! Sayısal değer giriniz.")
            sys.exit(1)  # Programı hata ile sonlandır
    
    # Para ekleme fonksiyonunu çağır
    add_test_money(amount)

