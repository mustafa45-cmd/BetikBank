# BetikBank - İnternet Bankacılığı Projesi

Modern ve güvenli bir internet bankacılığı uygulaması. Python Flask framework'ü kullanılarak geliştirilmiştir.

## Özellikler

- 🔐 **Kullanıcı Yönetimi**: Kayıt olma, giriş yapma ve profil yönetimi
- 💳 **Hesap Yönetimi**: Hesap görüntüleme ve yönetimi
- 💸 **Para Transferi**: Güvenli ve hızlı para transferi işlemleri
- 📊 **İşlem Geçmişi**: Detaylı işlem geçmişi görüntüleme
- 🔒 **Güvenlik**: Şifre hashleme ve kullanıcı oturum yönetimi

## Gereksinimler

- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)

## Kurulum

1. Projeyi klonlayın veya indirin:
```bash
cd BETİK
```

2. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

3. Uygulamayı çalıştırın:
```bash
python app.py
```

4. Tarayıcınızda şu adrese gidin:
```
http://localhost:5000
```

## Kullanım

### İlk Kullanım

1. Ana sayfada "Kayıt Ol" butonuna tıklayın
2. Gerekli bilgileri doldurun (TC Kimlik No, Ad, Soyad, E-posta, Telefon, Şifre)
3. Kayıt olduktan sonra otomatik olarak bir hesap oluşturulacaktır
4. Giriş yaparak dashboard'a erişebilirsiniz

### Para Transferi

1. Dashboard'dan "Para Transferi" sayfasına gidin
2. Gönderen hesabınızı seçin
3. Alıcı hesap numarasını girin (16 haneli)
4. Transfer tutarını ve açıklamayı girin
5. "Transfer Et" butonuna tıklayın

### İşlem Geçmişi

1. "İşlemlerim" menüsünden tüm işlemlerinizi görüntüleyebilirsiniz
2. Belirli bir hesaba göre filtreleme yapabilirsiniz

## Veritabanı

Uygulama SQLite veritabanı kullanmaktadır. İlk çalıştırmada `betikbank.db` dosyası otomatik olarak oluşturulacaktır.

### Veritabanı Modelleri

- **User**: Kullanıcı bilgileri
- **Hesap**: Hesap bilgileri ve bakiyeler
- **Islem**: Para transferi işlem kayıtları

## Güvenlik Notları

⚠️ **ÖNEMLİ**: Bu uygulama eğitim/öğrenme amaçlıdır. Gerçek bir bankacılık uygulaması için:

- Production ortamında `SECRET_KEY` değiştirilmelidir
- HTTPS kullanılmalıdır
- Daha güçlü şifre politikaları uygulanmalıdır
- İki faktörlü kimlik doğrulama eklenmelidir
- Rate limiting ve DDoS koruması eklenmelidir
- Veritabanı şifreleme kullanılmalıdır
- Güvenlik audit'i yapılmalıdır

## Geliştirme

Proje yapısı:
```
BETİK/
├── app.py                 # Ana uygulama dosyası
├── requirements.txt       # Python bağımlılıkları
├── betikbank.db          # SQLite veritabanı (otomatik oluşur)
├── templates/            # HTML şablonları
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── transfer.html
│   ├── transactions.html
│   ├── account_detail.html
│   └── profile.html
└── static/               # Statik dosyalar
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## Lisans

Bu proje eğitim amaçlıdır.

## İletişim

Sorularınız için issue açabilirsiniz.


