"""
Test için mevcut kullanıcıların hesaplarına para ekleme scripti
"""
from app import app, db, User, Hesap

def add_test_money(amount=10000.0):
    """Tüm kullanıcıların vadesiz hesaplarına para ekler"""
    with app.app_context():
        # Tüm kullanıcıları al
        users = User.query.all()
        
        if not users:
            print("Hiç kullanıcı bulunamadı!")
            return
        
        print(f"Toplam {len(users)} kullanıcı bulundu.")
        print(f"Her kullanıcıya {amount:.2f} TL ekleniyor...\n")
        
        updated_count = 0
        
        for user in users:
            # Her kullanıcının vadesiz hesaplarını bul
            vadesiz_hesaplar = Hesap.query.filter_by(
                kullanici_id=user.id,
                hesap_turu='Vadesiz'
            ).all()
            
            if vadesiz_hesaplar:
                # İlk vadesiz hesaba para ekle
                hesap = vadesiz_hesaplar[0]
                eski_bakiye = hesap.bakiye
                hesap.bakiye += amount
                
                db.session.commit()
                
                print(f"[OK] {user.ad} {user.soyad} ({user.tc_no})")
                print(f"  Hesap: {hesap.hesap_no}")
                print(f"  Eski bakiye: {eski_bakiye:.2f} TL -> Yeni bakiye: {hesap.bakiye:.2f} TL\n")
                updated_count += 1
            else:
                # Vadesiz hesap yoksa yeni hesap oluştur
                hesap_no = f"{user.tc_no}{user.id:05d}"[:16]
                yeni_hesap = Hesap(
                    hesap_no=hesap_no,
                    kullanici_id=user.id,
                    bakiye=amount,
                    hesap_turu='Vadesiz'
                )
                db.session.add(yeni_hesap)
                db.session.commit()
                
                print(f"[OK] {user.ad} {user.soyad} ({user.tc_no}) - YENI HESAP OLUSTURULDU")
                print(f"  Hesap: {yeni_hesap.hesap_no}")
                print(f"  Bakiye: {amount:.2f} TL\n")
                updated_count += 1
        
        print(f"\n[Tamamlandi] Islem tamamlandi! {updated_count} kullaniciya para eklendi.")

if __name__ == '__main__':
    import sys
    
    # Komut satırından miktar al (varsayılan 10.000 TL)
    amount = 10000.0
    if len(sys.argv) > 1:
        try:
            amount = float(sys.argv[1])
        except ValueError:
            print("Geçersiz miktar! Sayısal değer giriniz.")
            sys.exit(1)
    
    add_test_money(amount)

