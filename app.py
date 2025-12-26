# Flask ve gerekli kütüphaneleri import et
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy  # Veritabanı ORM için
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user  # Kullanıcı oturum yönetimi için
from werkzeug.security import generate_password_hash, check_password_hash  # Şifre hashleme için
from werkzeug.utils import secure_filename  # Dosya adı güvenliği için
from datetime import datetime, timedelta  # Tarih/saat işlemleri için
import os  # İşletim sistemi işlemleri için
import random  # Rastgele sayı üretimi için

# Flask uygulamasını oluştur
app = Flask(__name__)

# Uygulama yapılandırmaları
app.config['SECRET_KEY'] = 'betikbank-secret-key-change-in-production'  # Session ve CSRF koruması için gizli anahtar
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///betikbank.db'  # SQLite veritabanı bağlantı adresi
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Performans için modifikasyon takibini kapat

# Veritabanı ve login manager'ı başlat
db = SQLAlchemy(app)  # SQLAlchemy ORM nesnesi
login_manager = LoginManager()  # Login manager nesnesi
login_manager.init_app(app)  # Login manager'ı uygulamaya bağla
login_manager.login_view = 'login'  # Giriş gerektiren sayfalarda yönlendirilecek sayfa
login_manager.login_message = 'Bu sayfaya erişmek için giriş yapmalısınız.'  # Giriş gerektiren sayfalarda gösterilecek mesaj

# ============================================
# VERİTABANI MODELLERİ
# ============================================

# Kullanıcı modeli - Sistemdeki tüm kullanıcıları temsil eder
class User(UserMixin, db.Model):
    """Kullanıcı bilgilerini saklayan veritabanı modeli"""
    id = db.Column(db.Integer, primary_key=True)  # Birincil anahtar
    tc_no = db.Column(db.String(11), unique=True, nullable=False)  # TC Kimlik Numarası (benzersiz, zorunlu)
    ad = db.Column(db.String(100), nullable=False)  # Kullanıcı adı
    soyad = db.Column(db.String(100), nullable=False)  # Kullanıcı soyadı
    email = db.Column(db.String(120), unique=True, nullable=False)  # E-posta adresi (benzersiz, zorunlu)
    telefon = db.Column(db.String(15), nullable=False)  # Telefon numarası
    password_hash = db.Column(db.String(255), nullable=False)  # Hashlenmiş şifre (düz metin saklanmaz)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Hesap oluşturulma tarihi
    
    # İlişkiler - Bir kullanıcının birden fazla hesabı, kartı ve yatırım hesabı olabilir
    hesaplar = db.relationship('Hesap', backref='kullanici', lazy=True)  # Kullanıcının hesapları
    kartlar = db.relationship('Kart', backref='kullanici', lazy=True)  # Kullanıcının kartları
    yatirim_hesaplari = db.relationship('YatirimHesabi', backref='kullanici', lazy=True)  # Kullanıcının yatırım hesapları

# Hesap modeli - Banka hesaplarını temsil eder
class Hesap(db.Model):
    """Banka hesaplarını saklayan veritabanı modeli"""
    id = db.Column(db.Integer, primary_key=True)  # Birincil anahtar
    hesap_no = db.Column(db.String(16), unique=True, nullable=False)  # Hesap numarası (benzersiz, 16 haneli)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Hesabın sahibi (yabancı anahtar)
    bakiye = db.Column(db.Float, default=0.0, nullable=False)  # Hesap bakiyesi (varsayılan: 0.0)
    hesap_turu = db.Column(db.String(20), default='Vadesiz', nullable=False)  # Hesap türü (Vadesiz, Vadeli vb.)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Hesap oluşturulma tarihi
    
    # İlişkiler - Bir hesabın birden fazla işlemi ve kartı olabilir
    gonderilen_islemler = db.relationship('Islem', foreign_keys='Islem.gonderen_hesap_id', backref='gonderen_hesap', lazy=True)  # Bu hesaptan gönderilen işlemler
    alinan_islemler = db.relationship('Islem', foreign_keys='Islem.alici_hesap_id', backref='alici_hesap', lazy=True)  # Bu hesaba gelen işlemler
    kartlar = db.relationship('Kart', backref='hesap', lazy=True)  # Bu hesaba bağlı kartlar

# İşlem modeli - Para transferi ve diğer işlemleri temsil eder
class Islem(db.Model):
    """Para transferi ve diğer işlemleri saklayan veritabanı modeli"""
    id = db.Column(db.Integer, primary_key=True)  # Birincil anahtar
    gonderen_hesap_id = db.Column(db.Integer, db.ForeignKey('hesap.id'), nullable=False)  # Gönderen hesap (yabancı anahtar)
    alici_hesap_id = db.Column(db.Integer, db.ForeignKey('hesap.id'), nullable=False)  # Alıcı hesap (yabancı anahtar)
    tutar = db.Column(db.Float, nullable=False)  # İşlem tutarı
    aciklama = db.Column(db.String(200))  # İşlem açıklaması (opsiyonel)
    islem_turu = db.Column(db.String(20), default='Transfer', nullable=False)  # İşlem türü (Transfer, Yatırım vb.)
    tarih = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # İşlem tarihi

# Kart modeli - Banka kartlarını temsil eder
class Kart(db.Model):
    """Banka kartlarını saklayan veritabanı modeli"""
    id = db.Column(db.Integer, primary_key=True)  # Birincil anahtar
    kart_no = db.Column(db.String(16), unique=True, nullable=False)  # Kart numarası (benzersiz, 16 haneli)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Kart sahibi (yabancı anahtar)
    hesap_id = db.Column(db.Integer, db.ForeignKey('hesap.id'), nullable=False)  # Bağlı hesap (yabancı anahtar)
    kart_turu = db.Column(db.String(20), nullable=False)  # Kart türü: Kredi Kartı, Banka Kartı, Sanal Kart
    son_kullanim_tarihi = db.Column(db.String(5), nullable=False)  # Son kullanım tarihi (MM/YY formatında)
    cvv = db.Column(db.String(3), nullable=False)  # CVV güvenlik kodu (3 haneli)
    kart_sahibi_adi = db.Column(db.String(100), nullable=False)  # Kart üzerindeki isim
    limit = db.Column(db.Float, default=0.0)  # Kredi kartı limiti (sadece kredi kartları için)
    durum = db.Column(db.String(20), default='Aktif', nullable=False)  # Kart durumu: Aktif, Pasif, İptal
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Kart oluşturulma tarihi

# Yatırım Hesabı modeli - Yatırım hesaplarını temsil eder
class YatirimHesabi(db.Model):
    """Yatırım hesaplarını saklayan veritabanı modeli"""
    id = db.Column(db.Integer, primary_key=True)  # Birincil anahtar
    hesap_no = db.Column(db.String(16), unique=True, nullable=False)  # Yatırım hesap numarası (benzersiz)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Hesap sahibi (yabancı anahtar)
    yatirim_turu = db.Column(db.String(50), nullable=False)  # Yatırım türü: Döviz, Altın, Borsa, Fon, Kripto Para
    toplam_bakiye = db.Column(db.Float, default=0.0, nullable=False)  # Toplam yatırım bakiyesi
    kar_zarar = db.Column(db.Float, default=0.0)  # Toplam kar/zarar miktarı
    durum = db.Column(db.String(20), default='Aktif', nullable=False)  # Hesap durumu: Aktif, Pasif
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Hesap oluşturulma tarihi

# ============================================
# KULLANICI YÜKLEME FONKSİYONU
# ============================================

# Flask-Login için kullanıcı yükleme fonksiyonu
@login_manager.user_loader
def load_user(user_id):
    """Session'dan kullanıcı ID'sini alıp kullanıcı nesnesini döndürür"""
    return User.query.get(int(user_id))

# ============================================
# ROUTE FONKSİYONLARI
# ============================================

# Ana Sayfa - Giriş yapılmamışsa ana sayfa, yapılmışsa dashboard'a yönlendir
@app.route('/')
def index():
    """Ana sayfa route'u - Giriş yapılmışsa dashboard'a yönlendirir"""
    if current_user.is_authenticated:  # Kullanıcı giriş yapmışsa
        return redirect(url_for('dashboard'))  # Dashboard'a yönlendir
    return render_template('index.html')  # Giriş yapılmamışsa ana sayfayı göster

# Kayıt Ol - Yeni kullanıcı kaydı için route
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Kullanıcı kayıt sayfası - GET: form gösterir, POST: kayıt işlemini yapar"""
    if request.method == 'POST':  # Form gönderildiyse
        # Form verilerini al
        tc_no = request.form.get('tc_no')
        ad = request.form.get('ad')
        soyad = request.form.get('soyad')
        email = request.form.get('email')
        telefon = request.form.get('telefon')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Validasyon kontrolleri
        # TC Kimlik Numarası kontrolü - Aynı TC ile kayıt var mı?
        if User.query.filter_by(tc_no=tc_no).first():
            flash('Bu TC Kimlik Numarası ile zaten bir hesap bulunmaktadır.', 'error')
            return redirect(url_for('register'))
        
        # E-posta kontrolü - Aynı e-posta ile kayıt var mı?
        if User.query.filter_by(email=email).first():
            flash('Bu e-posta adresi ile zaten bir hesap bulunmaktadır.', 'error')
            return redirect(url_for('register'))
        
        # Şifre eşleşme kontrolü
        if password != password_confirm:
            flash('Şifreler eşleşmiyor.', 'error')
            return redirect(url_for('register'))
        
        # TC Kimlik Numarası format kontrolü - 11 haneli ve sadece rakam olmalı
        if len(tc_no) != 11 or not tc_no.isdigit():
            flash('TC Kimlik Numarası 11 haneli olmalıdır.', 'error')
            return redirect(url_for('register'))
        
        # Yeni kullanıcı oluştur
        new_user = User(
            tc_no=tc_no,
            ad=ad,
            soyad=soyad,
            email=email,
            telefon=telefon,
            password_hash=generate_password_hash(password)  # Şifreyi hashle ve sakla
        )
        
        db.session.add(new_user)  # Kullanıcıyı veritabanına ekle
        db.session.commit()  # Değişiklikleri kaydet
        
        # Otomatik hesap oluştur - Her yeni kullanıcıya otomatik vadesiz hesap açılır
        hesap_no = f"{tc_no}{new_user.id:05d}"[:16]  # TC + kullanıcı ID'sinden hesap numarası oluştur
        new_hesap = Hesap(
            hesap_no=hesap_no,
            kullanici_id=new_user.id,
            bakiye=0.0,  # Başlangıç bakiyesi sıfır
            hesap_turu='Vadesiz'
        )
        
        db.session.add(new_hesap)  # Hesabı veritabanına ekle
        db.session.commit()  # Değişiklikleri kaydet
        
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))  # Giriş sayfasına yönlendir
    
    return render_template('register.html')  # GET isteği için kayıt formunu göster

# Giriş Yap - Kullanıcı girişi için route
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Kullanıcı giriş sayfası - GET: form gösterir, POST: giriş işlemini yapar"""
    if request.method == 'POST':  # Form gönderildiyse
        # Form verilerini al
        tc_no = request.form.get('tc_no')
        password = request.form.get('password')
        
        # Kullanıcıyı veritabanında ara
        user = User.query.filter_by(tc_no=tc_no).first()
        
        # Kullanıcı var mı ve şifre doğru mu kontrol et
        if user and check_password_hash(user.password_hash, password):
            login_user(user)  # Kullanıcıyı oturuma al
            flash(f'Hoş geldiniz, {user.ad} {user.soyad}!', 'success')
            return redirect(url_for('dashboard'))  # Dashboard'a yönlendir
        else:
            flash('TC Kimlik Numarası veya şifre hatalı.', 'error')
    
    return render_template('login.html')  # GET isteği için giriş formunu göster

# Çıkış Yap - Kullanıcı oturumunu sonlandırır
@app.route('/logout')
@login_required  # Sadece giriş yapmış kullanıcılar erişebilir
def logout():
    """Kullanıcı çıkış işlemi - Oturumu sonlandırır ve ana sayfaya yönlendirir"""
    logout_user()  # Kullanıcı oturumunu kapat
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('index'))  # Ana sayfaya yönlendir

# Dashboard - Ana kontrol paneli
@app.route('/dashboard')
@login_required  # Sadece giriş yapmış kullanıcılar erişebilir
def dashboard():
    """Kullanıcı dashboard sayfası - Hesaplar, kartlar, yatırımlar ve son işlemleri gösterir"""
    # Kullanıcının tüm hesaplarını getir
    hesaplar = Hesap.query.filter_by(kullanici_id=current_user.id).all()
    
    # Kullanıcının aktif kartlarını getir (en yeni olanlar önce)
    kartlar = Kart.query.filter_by(kullanici_id=current_user.id, durum='Aktif').order_by(Kart.created_at.desc()).all()
    
    # Kullanıcının aktif yatırım hesaplarını getir (en yeni olanlar önce)
    yatirim_hesaplari = YatirimHesabi.query.filter_by(kullanici_id=current_user.id, durum='Aktif').order_by(YatirimHesabi.created_at.desc()).all()
    
    # Son işlemleri topla - Her hesaptan son 5 gönderilen ve alınan işlemi al
    son_islemler = []
    for hesap in hesaplar:
        gonderilen = Islem.query.filter_by(gonderen_hesap_id=hesap.id).order_by(Islem.tarih.desc()).limit(5).all()  # Son 5 gönderilen işlem
        alinan = Islem.query.filter_by(alici_hesap_id=hesap.id).order_by(Islem.tarih.desc()).limit(5).all()  # Son 5 alınan işlem
        son_islemler.extend(gonderilen + alinan)  # Listeye ekle
    
    # İşlemleri tarihe göre sırala (en yeni olanlar önce)
    son_islemler.sort(key=lambda x: x.tarih, reverse=True)
    son_islemler = son_islemler[:10]  # En son 10 işlemi al
    
    return render_template('dashboard.html', hesaplar=hesaplar, kartlar=kartlar, yatirim_hesaplari=yatirim_hesaplari, son_islemler=son_islemler)

# Para Transferi - Hesaplar arası para transferi
@app.route('/transfer', methods=['GET', 'POST'])
@login_required  # Sadece giriş yapmış kullanıcılar erişebilir
def transfer():
    """Para transferi sayfası - GET: form gösterir, POST: transfer işlemini yapar"""
    # Kullanıcının hesaplarını getir
    hesaplar = Hesap.query.filter_by(kullanici_id=current_user.id).all()
    
    if request.method == 'POST':  # Form gönderildiyse
        # Form verilerini al
        gonderen_hesap_id = request.form.get('gonderen_hesap')
        alici_hesap_no = request.form.get('alici_hesap_no')
        tutar = float(request.form.get('tutar'))
        aciklama = request.form.get('aciklama', '')  # Açıklama opsiyonel
        
        # Validasyon kontrolleri
        # Gönderen hesap kontrolü - Hesap var mı ve kullanıcıya ait mi?
        gonderen_hesap = Hesap.query.get(gonderen_hesap_id)
        if not gonderen_hesap or gonderen_hesap.kullanici_id != current_user.id:
            flash('Geçersiz gönderen hesap.', 'error')
            return redirect(url_for('transfer'))
        
        # Alıcı hesap kontrolü - Hesap bulunuyor mu?
        alici_hesap = Hesap.query.filter_by(hesap_no=alici_hesap_no).first()
        if not alici_hesap:
            flash('Alıcı hesap bulunamadı.', 'error')
            return redirect(url_for('transfer'))
        
        # Aynı hesaba transfer kontrolü - Kendi hesabına transfer yapılamaz
        if gonderen_hesap.id == alici_hesap.id:
            flash('Kendi hesabınıza transfer yapamazsınız.', 'error')
            return redirect(url_for('transfer'))
        
        # Tutar kontrolü - Tutar pozitif olmalı
        if tutar <= 0:
            flash('Transfer tutarı 0\'dan büyük olmalıdır.', 'error')
            return redirect(url_for('transfer'))
        
        # Bakiye kontrolü - Yeterli bakiye var mı?
        if gonderen_hesap.bakiye < tutar:
            flash('Yetersiz bakiye.', 'error')
            return redirect(url_for('transfer'))
        
        # Transfer işlemi - Bakiyeleri güncelle
        gonderen_hesap.bakiye -= tutar  # Gönderen hesaptan düş
        alici_hesap.bakiye += tutar  # Alıcı hesaba ekle
        
        # İşlem kaydı oluştur
        yeni_islem = Islem(
            gonderen_hesap_id=gonderen_hesap.id,
            alici_hesap_id=alici_hesap.id,
            tutar=tutar,
            aciklama=aciklama,
            islem_turu='Transfer'
        )
        
        db.session.add(yeni_islem)  # İşlemi veritabanına ekle
        db.session.commit()  # Değişiklikleri kaydet
        
        flash(f'{tutar:.2f} TL başarıyla transfer edildi.', 'success')
        return redirect(url_for('dashboard'))  # Dashboard'a yönlendir
    
    return render_template('transfer.html', hesaplar=hesaplar)  # GET isteği için transfer formunu göster

# İşlem Geçmişi - Tüm işlemleri görüntüleme
@app.route('/transactions')
@login_required  # Sadece giriş yapmış kullanıcılar erişebilir
def transactions():
    """İşlem geçmişi sayfası - Tüm hesaplardan veya seçili hesaptan işlemleri gösterir"""
    # Kullanıcının tüm hesaplarını getir
    hesaplar = Hesap.query.filter_by(kullanici_id=current_user.id).all()
    
    # URL parametresinden hesap ID'sini al (filtreleme için)
    hesap_id = request.args.get('hesap_id', type=int)
    
    if hesap_id:  # Belirli bir hesap seçilmişse
        hesap = Hesap.query.get(hesap_id)
        # Hesap var mı ve kullanıcıya ait mi kontrol et
        if hesap and hesap.kullanici_id == current_user.id:
            gonderilen = Islem.query.filter_by(gonderen_hesap_id=hesap.id).order_by(Islem.tarih.desc()).all()  # Bu hesaptan gönderilen işlemler
            alinan = Islem.query.filter_by(alici_hesap_id=hesap.id).order_by(Islem.tarih.desc()).all()  # Bu hesaba gelen işlemler
            islemler = sorted(gonderilen + alinan, key=lambda x: x.tarih, reverse=True)  # Tarihe göre sırala
        else:
            islemler = []  # Geçersiz hesap seçilmişse boş liste
    else:
        # Tüm hesaplardan işlemleri getir
        islemler = []
        for hesap in hesaplar:
            gonderilen = Islem.query.filter_by(gonderen_hesap_id=hesap.id).all()  # Gönderilen işlemler
            alinan = Islem.query.filter_by(alici_hesap_id=hesap.id).all()  # Alınan işlemler
            islemler.extend(gonderilen + alinan)  # Listeye ekle
        
        islemler.sort(key=lambda x: x.tarih, reverse=True)  # Tarihe göre sırala (en yeni önce)
    
    return render_template('transactions.html', hesaplar=hesaplar, islemler=islemler, selected_hesap_id=hesap_id)

# Hesap Detayları - Belirli bir hesabın detaylarını göster
@app.route('/account/<int:hesap_id>')
@login_required  # Sadece giriş yapmış kullanıcılar erişebilir
def account_detail(hesap_id):
    """Hesap detay sayfası - Hesap bilgilerini ve işlem geçmişini gösterir"""
    # Hesabı veritabanından getir (yoksa 404 hatası)
    hesap = Hesap.query.get_or_404(hesap_id)
    
    # Yetki kontrolü - Hesap kullanıcıya ait mi?
    if hesap.kullanici_id != current_user.id:
        flash('Bu hesaba erişim yetkiniz yok.', 'error')
        return redirect(url_for('dashboard'))
    
    # Bu hesaptan gönderilen ve alınan tüm işlemleri getir
    gonderilen = Islem.query.filter_by(gonderen_hesap_id=hesap.id).order_by(Islem.tarih.desc()).all()  # Gönderilen işlemler
    alinan = Islem.query.filter_by(alici_hesap_id=hesap.id).order_by(Islem.tarih.desc()).all()  # Alınan işlemler
    islemler = sorted(gonderilen + alinan, key=lambda x: x.tarih, reverse=True)  # Tarihe göre sırala
    
    return render_template('account_detail.html', hesap=hesap, islemler=islemler)

# Profil - Kullanıcı profil bilgilerini göster
@app.route('/profile')
@login_required  # Sadece giriş yapmış kullanıcılar erişebilir
def profile():
    """Kullanıcı profil sayfası - Kullanıcı bilgilerini gösterir"""
    return render_template('profile.html', user=current_user)

# Kartlar - Kullanıcının tüm kartlarını listele
@app.route('/cards')
@login_required  # Sadece giriş yapmış kullanıcılar erişebilir
def cards():
    """Kartlar listesi sayfası - Kullanıcının tüm kartlarını gösterir"""
    # Kullanıcının tüm kartlarını getir (en yeni olanlar önce)
    kartlar = Kart.query.filter_by(kullanici_id=current_user.id).order_by(Kart.created_at.desc()).all()
    return render_template('cards.html', kartlar=kartlar)

# Yeni Kart Oluştur - Yeni banka kartı oluşturma
@app.route('/cards/new', methods=['GET', 'POST'])
@login_required  # Sadece giriş yapmış kullanıcılar erişebilir
def new_card():
    """Yeni kart oluşturma sayfası - GET: form gösterir, POST: kart oluşturur"""
    # Kullanıcının hesaplarını getir (kart bağlanacak hesap seçimi için)
    hesaplar = Hesap.query.filter_by(kullanici_id=current_user.id).all()
    
    if request.method == 'POST':  # Form gönderildiyse
        # Form verilerini al
        hesap_id = request.form.get('hesap_id')
        kart_turu = request.form.get('kart_turu')
        
        # Hesap kontrolü - Hesap var mı ve kullanıcıya ait mi?
        hesap = Hesap.query.get(hesap_id)
        if not hesap or hesap.kullanici_id != current_user.id:
            flash('Geçersiz hesap seçimi.', 'error')
            return redirect(url_for('new_card'))
        
        # Kart numarası oluştur (16 haneli, benzersiz olmalı)
        kart_no = ''.join([str(random.randint(0, 9)) for _ in range(16)])
        # Benzersizlik kontrolü - Aynı kart numarası varsa yeniden oluştur
        while Kart.query.filter_by(kart_no=kart_no).first():
            kart_no = ''.join([str(random.randint(0, 9)) for _ in range(16)])
        
        # Son kullanım tarihi hesapla (3 yıl sonra)
        son_kullanim = datetime.now() + timedelta(days=3*365)
        son_kullanim_str = son_kullanim.strftime('%m/%y')  # MM/YY formatında
        
        # CVV oluştur (3 haneli rastgele sayı)
        cvv = ''.join([str(random.randint(0, 9)) for _ in range(3)])
        
        # Limit belirleme - Sadece kredi kartları için limit var
        limit = 0.0
        if kart_turu == 'Kredi Kartı':
            limit = float(request.form.get('limit', 10000))  # Varsayılan limit: 10000 TL
        
        # Yeni kart oluştur
        yeni_kart = Kart(
            kart_no=kart_no,
            kullanici_id=current_user.id,
            hesap_id=hesap_id,
            kart_turu=kart_turu,
            son_kullanim_tarihi=son_kullanim_str,
            cvv=cvv,
            kart_sahibi_adi=f"{current_user.ad} {current_user.soyad}",  # Kart sahibi adı
            limit=limit,
            durum='Aktif'  # Yeni kartlar aktif olarak oluşturulur
        )
        
        db.session.add(yeni_kart)  # Kartı veritabanına ekle
        db.session.commit()  # Değişiklikleri kaydet
        
        flash(f'{kart_turu} başarıyla oluşturuldu!', 'success')
        return redirect(url_for('cards'))  # Kartlar sayfasına yönlendir
    
    return render_template('new_card.html', hesaplar=hesaplar)  # GET isteği için form göster

# Yatırım Hesapları - Kullanıcının yatırım hesaplarını listele
@app.route('/investment')
@login_required  # Sadece giriş yapmış kullanıcılar erişebilir
def investment():
    """Yatırım hesapları listesi sayfası - Kullanıcının tüm yatırım hesaplarını gösterir"""
    # Kullanıcının tüm yatırım hesaplarını getir (en yeni olanlar önce)
    yatirim_hesaplari = YatirimHesabi.query.filter_by(kullanici_id=current_user.id).order_by(YatirimHesabi.created_at.desc()).all()
    return render_template('investment.html', yatirim_hesaplari=yatirim_hesaplari)

# Yeni Yatırım Hesabı Aç - Yeni yatırım hesabı oluşturma
@app.route('/investment/new', methods=['GET', 'POST'])
@login_required  # Sadece giriş yapmış kullanıcılar erişebilir
def new_investment():
    """Yeni yatırım hesabı açma sayfası - GET: form gösterir, POST: hesap açar"""
    if request.method == 'POST':  # Form gönderildiyse
        # Form verilerini al
        yatirim_turu = request.form.get('yatirim_turu')
        baslangic_tutar = float(request.form.get('baslangic_tutar', 0))  # Başlangıç tutarı (opsiyonel)
        
        # Hesap numarası oluştur (Y + TC'nin son 8 hanesi + 4 haneli rastgele sayı)
        hesap_no = f"Y{current_user.tc_no[-8:]}{random.randint(1000, 9999)}"
        # Benzersizlik kontrolü - Aynı hesap numarası varsa yeniden oluştur
        while YatirimHesabi.query.filter_by(hesap_no=hesap_no).first():
            hesap_no = f"Y{current_user.tc_no[-8:]}{random.randint(1000, 9999)}"
        
        # Ana hesaptan para çek (eğer başlangıç tutarı belirtilmişse)
        if baslangic_tutar > 0:
            # Vadesiz hesabı bul
            ana_hesap = Hesap.query.filter_by(kullanici_id=current_user.id, hesap_turu='Vadesiz').first()
            if not ana_hesap:
                flash('Vadesiz hesabınız bulunamadı.', 'error')
                return redirect(url_for('new_investment'))
            
            # Bakiye kontrolü - Yeterli bakiye var mı?
            if ana_hesap.bakiye < baslangic_tutar:
                flash('Yetersiz bakiye. Yatırım hesabını başlangıç tutarı olmadan açabilirsiniz.', 'error')
                return redirect(url_for('new_investment'))
            
            # Vadesiz hesaptan para çek
            ana_hesap.bakiye -= baslangic_tutar
            
            # İşlem kaydı oluştur
            yeni_islem = Islem(
                gonderen_hesap_id=ana_hesap.id,
                alici_hesap_id=ana_hesap.id,  # Yatırım hesabına geçti sayılır (aynı hesap)
                tutar=baslangic_tutar,
                aciklama=f'Yatırım Hesabı Açılışı - {yatirim_turu}',
                islem_turu='Yatırım'
            )
            db.session.add(yeni_islem)  # İşlemi veritabanına ekle
        
        # Yeni yatırım hesabı oluştur
        yeni_yatirim = YatirimHesabi(
            hesap_no=hesap_no,
            kullanici_id=current_user.id,
            yatirim_turu=yatirim_turu,
            toplam_bakiye=baslangic_tutar,  # Başlangıç bakiyesi
            kar_zarar=0.0,  # Başlangıçta kar/zarar yok
            durum='Aktif'  # Yeni hesaplar aktif olarak açılır
        )
        
        db.session.add(yeni_yatirim)  # Yatırım hesabını veritabanına ekle
        db.session.commit()  # Değişiklikleri kaydet
        
        flash(f'{yatirim_turu} yatırım hesabı başarıyla açıldı!', 'success')
        return redirect(url_for('investment'))  # Yatırım hesapları sayfasına yönlendir
    
    # GET isteği için toplam bakiyeyi hesapla (formda gösterilmek üzere)
    hesaplar = Hesap.query.filter_by(kullanici_id=current_user.id).all()
    toplam_bakiye = sum([h.bakiye for h in hesaplar])  # Tüm hesapların toplam bakiyesi
    return render_template('new_investment.html', toplam_bakiye=toplam_bakiye)

# Kart Detay - Belirli bir kartın detaylarını göster
@app.route('/card/<int:kart_id>')
@login_required  # Sadece giriş yapmış kullanıcılar erişebilir
def card_detail(kart_id):
    """Kart detay sayfası - Kart bilgilerini gösterir"""
    # Kartı veritabanından getir (yoksa 404 hatası)
    kart = Kart.query.get_or_404(kart_id)
    
    # Yetki kontrolü - Kart kullanıcıya ait mi?
    if kart.kullanici_id != current_user.id:
        flash('Bu karta erişim yetkiniz yok.', 'error')
        return redirect(url_for('cards'))
    
    return render_template('card_detail.html', kart=kart)

# Yatırım Hesabı Detay - Belirli bir yatırım hesabının detaylarını göster
@app.route('/investment/<int:yatirim_id>')
@login_required  # Sadece giriş yapmış kullanıcılar erişebilir
def investment_detail(yatirim_id):
    """Yatırım hesabı detay sayfası - Yatırım hesabı bilgilerini gösterir"""
    # Yatırım hesabını veritabanından getir (yoksa 404 hatası)
    yatirim = YatirimHesabi.query.get_or_404(yatirim_id)
    
    # Yetki kontrolü - Yatırım hesabı kullanıcıya ait mi?
    if yatirim.kullanici_id != current_user.id:
        flash('Bu yatırım hesabına erişim yetkiniz yok.', 'error')
        return redirect(url_for('investment'))
    
    return render_template('investment_detail.html', yatirim=yatirim)

# ============================================
# UYGULAMA BAŞLATMA
# ============================================

# Uygulama doğrudan çalıştırılıyorsa (python app.py)
if __name__ == '__main__':
    # Uygulama bağlamı içinde veritabanı tablolarını oluştur
    with app.app_context():
        db.create_all()  # Tüm modeller için tabloları oluştur (yoksa)
    
    # Uygulamayı çalıştır
    # debug=True: Hata ayıklama modu açık (geliştirme için)
    # host='0.0.0.0': Tüm ağ arayüzlerinden erişilebilir
    # port=5000: 5000 portunda çalışır
    app.run(debug=True, host='0.0.0.0', port=5000)

