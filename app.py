from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'betikbank-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///betikbank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Bu sayfaya erişmek için giriş yapmalısınız.'

# Veritabanı Modelleri
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tc_no = db.Column(db.String(11), unique=True, nullable=False)
    ad = db.Column(db.String(100), nullable=False)
    soyad = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefon = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    hesaplar = db.relationship('Hesap', backref='kullanici', lazy=True)
    kartlar = db.relationship('Kart', backref='kullanici', lazy=True)
    yatirim_hesaplari = db.relationship('YatirimHesabi', backref='kullanici', lazy=True)

class Hesap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hesap_no = db.Column(db.String(16), unique=True, nullable=False)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bakiye = db.Column(db.Float, default=0.0, nullable=False)
    hesap_turu = db.Column(db.String(20), default='Vadesiz', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişkiler
    gonderilen_islemler = db.relationship('Islem', foreign_keys='Islem.gonderen_hesap_id', backref='gonderen_hesap', lazy=True)
    alinan_islemler = db.relationship('Islem', foreign_keys='Islem.alici_hesap_id', backref='alici_hesap', lazy=True)
    kartlar = db.relationship('Kart', backref='hesap', lazy=True)

class Islem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gonderen_hesap_id = db.Column(db.Integer, db.ForeignKey('hesap.id'), nullable=False)
    alici_hesap_id = db.Column(db.Integer, db.ForeignKey('hesap.id'), nullable=False)
    tutar = db.Column(db.Float, nullable=False)
    aciklama = db.Column(db.String(200))
    islem_turu = db.Column(db.String(20), default='Transfer', nullable=False)
    tarih = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Kart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kart_no = db.Column(db.String(16), unique=True, nullable=False)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    hesap_id = db.Column(db.Integer, db.ForeignKey('hesap.id'), nullable=False)
    kart_turu = db.Column(db.String(20), nullable=False)  # Kredi Kartı, Banka Kartı, Sanal Kart
    son_kullanim_tarihi = db.Column(db.String(5), nullable=False)  # MM/YY formatında
    cvv = db.Column(db.String(3), nullable=False)
    kart_sahibi_adi = db.Column(db.String(100), nullable=False)
    limit = db.Column(db.Float, default=0.0)  # Kredi kartı limiti
    durum = db.Column(db.String(20), default='Aktif', nullable=False)  # Aktif, Pasif, İptal
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class YatirimHesabi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hesap_no = db.Column(db.String(16), unique=True, nullable=False)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    yatirim_turu = db.Column(db.String(50), nullable=False)  # Döviz, Altın, Borsa, Fon
    toplam_bakiye = db.Column(db.Float, default=0.0, nullable=False)
    kar_zarar = db.Column(db.Float, default=0.0)  # Toplam kar/zarar
    durum = db.Column(db.String(20), default='Aktif', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ana Sayfa
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Kayıt Ol
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        tc_no = request.form.get('tc_no')
        ad = request.form.get('ad')
        soyad = request.form.get('soyad')
        email = request.form.get('email')
        telefon = request.form.get('telefon')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Validasyon
        if User.query.filter_by(tc_no=tc_no).first():
            flash('Bu TC Kimlik Numarası ile zaten bir hesap bulunmaktadır.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Bu e-posta adresi ile zaten bir hesap bulunmaktadır.', 'error')
            return redirect(url_for('register'))
        
        if password != password_confirm:
            flash('Şifreler eşleşmiyor.', 'error')
            return redirect(url_for('register'))
        
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
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Otomatik hesap oluştur
        hesap_no = f"{tc_no}{new_user.id:05d}"[:16]
        new_hesap = Hesap(
            hesap_no=hesap_no,
            kullanici_id=new_user.id,
            bakiye=0.0,
            hesap_turu='Vadesiz'
        )
        
        db.session.add(new_hesap)
        db.session.commit()
        
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Giriş Yap
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        tc_no = request.form.get('tc_no')
        password = request.form.get('password')
        
        user = User.query.filter_by(tc_no=tc_no).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Hoş geldiniz, {user.ad} {user.soyad}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('TC Kimlik Numarası veya şifre hatalı.', 'error')
    
    return render_template('login.html')

# Çıkış Yap
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('index'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    hesaplar = Hesap.query.filter_by(kullanici_id=current_user.id).all()
    kartlar = Kart.query.filter_by(kullanici_id=current_user.id, durum='Aktif').order_by(Kart.created_at.desc()).all()
    yatirim_hesaplari = YatirimHesabi.query.filter_by(kullanici_id=current_user.id, durum='Aktif').order_by(YatirimHesabi.created_at.desc()).all()
    
    # Son işlemler
    son_islemler = []
    for hesap in hesaplar:
        gonderilen = Islem.query.filter_by(gonderen_hesap_id=hesap.id).order_by(Islem.tarih.desc()).limit(5).all()
        alinan = Islem.query.filter_by(alici_hesap_id=hesap.id).order_by(Islem.tarih.desc()).limit(5).all()
        son_islemler.extend(gonderilen + alinan)
    
    son_islemler.sort(key=lambda x: x.tarih, reverse=True)
    son_islemler = son_islemler[:10]
    
    return render_template('dashboard.html', hesaplar=hesaplar, kartlar=kartlar, yatirim_hesaplari=yatirim_hesaplari, son_islemler=son_islemler)

# Para Transferi
@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    hesaplar = Hesap.query.filter_by(kullanici_id=current_user.id).all()
    
    if request.method == 'POST':
        gonderen_hesap_id = request.form.get('gonderen_hesap')
        alici_hesap_no = request.form.get('alici_hesap_no')
        tutar = float(request.form.get('tutar'))
        aciklama = request.form.get('aciklama', '')
        
        # Validasyon
        gonderen_hesap = Hesap.query.get(gonderen_hesap_id)
        if not gonderen_hesap or gonderen_hesap.kullanici_id != current_user.id:
            flash('Geçersiz gönderen hesap.', 'error')
            return redirect(url_for('transfer'))
        
        alici_hesap = Hesap.query.filter_by(hesap_no=alici_hesap_no).first()
        if not alici_hesap:
            flash('Alıcı hesap bulunamadı.', 'error')
            return redirect(url_for('transfer'))
        
        if gonderen_hesap.id == alici_hesap.id:
            flash('Kendi hesabınıza transfer yapamazsınız.', 'error')
            return redirect(url_for('transfer'))
        
        if tutar <= 0:
            flash('Transfer tutarı 0\'dan büyük olmalıdır.', 'error')
            return redirect(url_for('transfer'))
        
        if gonderen_hesap.bakiye < tutar:
            flash('Yetersiz bakiye.', 'error')
            return redirect(url_for('transfer'))
        
        # Transfer işlemi
        gonderen_hesap.bakiye -= tutar
        alici_hesap.bakiye += tutar
        
        # İşlem kaydı
        yeni_islem = Islem(
            gonderen_hesap_id=gonderen_hesap.id,
            alici_hesap_id=alici_hesap.id,
            tutar=tutar,
            aciklama=aciklama,
            islem_turu='Transfer'
        )
        
        db.session.add(yeni_islem)
        db.session.commit()
        
        flash(f'{tutar:.2f} TL başarıyla transfer edildi.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('transfer.html', hesaplar=hesaplar)

# İşlem Geçmişi
@app.route('/transactions')
@login_required
def transactions():
    hesaplar = Hesap.query.filter_by(kullanici_id=current_user.id).all()
    hesap_id = request.args.get('hesap_id', type=int)
    
    if hesap_id:
        hesap = Hesap.query.get(hesap_id)
        if hesap and hesap.kullanici_id == current_user.id:
            gonderilen = Islem.query.filter_by(gonderen_hesap_id=hesap.id).order_by(Islem.tarih.desc()).all()
            alinan = Islem.query.filter_by(alici_hesap_id=hesap.id).order_by(Islem.tarih.desc()).all()
            islemler = sorted(gonderilen + alinan, key=lambda x: x.tarih, reverse=True)
        else:
            islemler = []
    else:
        # Tüm işlemler
        islemler = []
        for hesap in hesaplar:
            gonderilen = Islem.query.filter_by(gonderen_hesap_id=hesap.id).all()
            alinan = Islem.query.filter_by(alici_hesap_id=hesap.id).all()
            islemler.extend(gonderilen + alinan)
        
        islemler.sort(key=lambda x: x.tarih, reverse=True)
    
    return render_template('transactions.html', hesaplar=hesaplar, islemler=islemler, selected_hesap_id=hesap_id)

# Hesap Detayları
@app.route('/account/<int:hesap_id>')
@login_required
def account_detail(hesap_id):
    hesap = Hesap.query.get_or_404(hesap_id)
    
    if hesap.kullanici_id != current_user.id:
        flash('Bu hesaba erişim yetkiniz yok.', 'error')
        return redirect(url_for('dashboard'))
    
    gonderilen = Islem.query.filter_by(gonderen_hesap_id=hesap.id).order_by(Islem.tarih.desc()).all()
    alinan = Islem.query.filter_by(alici_hesap_id=hesap.id).order_by(Islem.tarih.desc()).all()
    islemler = sorted(gonderilen + alinan, key=lambda x: x.tarih, reverse=True)
    
    return render_template('account_detail.html', hesap=hesap, islemler=islemler)

# Profil
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

# Kartlar
@app.route('/cards')
@login_required
def cards():
    kartlar = Kart.query.filter_by(kullanici_id=current_user.id).order_by(Kart.created_at.desc()).all()
    return render_template('cards.html', kartlar=kartlar)

# Yeni Kart Oluştur
@app.route('/cards/new', methods=['GET', 'POST'])
@login_required
def new_card():
    hesaplar = Hesap.query.filter_by(kullanici_id=current_user.id).all()
    
    if request.method == 'POST':
        hesap_id = request.form.get('hesap_id')
        kart_turu = request.form.get('kart_turu')
        
        hesap = Hesap.query.get(hesap_id)
        if not hesap or hesap.kullanici_id != current_user.id:
            flash('Geçersiz hesap seçimi.', 'error')
            return redirect(url_for('new_card'))
        
        # Kart numarası oluştur (16 haneli)
        kart_no = ''.join([str(random.randint(0, 9)) for _ in range(16)])
        while Kart.query.filter_by(kart_no=kart_no).first():
            kart_no = ''.join([str(random.randint(0, 9)) for _ in range(16)])
        
        # Son kullanım tarihi (3 yıl sonra)
        son_kullanim = datetime.now() + timedelta(days=3*365)
        son_kullanim_str = son_kullanim.strftime('%m/%y')
        
        # CVV oluştur
        cvv = ''.join([str(random.randint(0, 9)) for _ in range(3)])
        
        # Limit belirleme
        limit = 0.0
        if kart_turu == 'Kredi Kartı':
            limit = float(request.form.get('limit', 10000))
        
        # Yeni kart oluştur
        yeni_kart = Kart(
            kart_no=kart_no,
            kullanici_id=current_user.id,
            hesap_id=hesap_id,
            kart_turu=kart_turu,
            son_kullanim_tarihi=son_kullanim_str,
            cvv=cvv,
            kart_sahibi_adi=f"{current_user.ad} {current_user.soyad}",
            limit=limit,
            durum='Aktif'
        )
        
        db.session.add(yeni_kart)
        db.session.commit()
        
        flash(f'{kart_turu} başarıyla oluşturuldu!', 'success')
        return redirect(url_for('cards'))
    
    return render_template('new_card.html', hesaplar=hesaplar)

# Yatırım Hesapları
@app.route('/investment')
@login_required
def investment():
    yatirim_hesaplari = YatirimHesabi.query.filter_by(kullanici_id=current_user.id).order_by(YatirimHesabi.created_at.desc()).all()
    return render_template('investment.html', yatirim_hesaplari=yatirim_hesaplari)

# Yeni Yatırım Hesabı Aç
@app.route('/investment/new', methods=['GET', 'POST'])
@login_required
def new_investment():
    if request.method == 'POST':
        yatirim_turu = request.form.get('yatirim_turu')
        baslangic_tutar = float(request.form.get('baslangic_tutar', 0))
        
        # Hesap numarası oluştur
        hesap_no = f"Y{current_user.tc_no[-8:]}{random.randint(1000, 9999)}"
        while YatirimHesabi.query.filter_by(hesap_no=hesap_no).first():
            hesap_no = f"Y{current_user.tc_no[-8:]}{random.randint(1000, 9999)}"
        
        # Ana hesaptan para çek (eğer başlangıç tutarı varsa)
        if baslangic_tutar > 0:
            ana_hesap = Hesap.query.filter_by(kullanici_id=current_user.id, hesap_turu='Vadesiz').first()
            if not ana_hesap:
                flash('Vadesiz hesabınız bulunamadı.', 'error')
                return redirect(url_for('new_investment'))
            
            if ana_hesap.bakiye < baslangic_tutar:
                flash('Yetersiz bakiye. Yatırım hesabını başlangıç tutarı olmadan açabilirsiniz.', 'error')
                return redirect(url_for('new_investment'))
            
            ana_hesap.bakiye -= baslangic_tutar
            
            # İşlem kaydı
            yeni_islem = Islem(
                gonderen_hesap_id=ana_hesap.id,
                alici_hesap_id=ana_hesap.id,  # Yatırım hesabına geçti sayılır
                tutar=baslangic_tutar,
                aciklama=f'Yatırım Hesabı Açılışı - {yatirim_turu}',
                islem_turu='Yatırım'
            )
            db.session.add(yeni_islem)
        
        # Yeni yatırım hesabı oluştur
        yeni_yatirim = YatirimHesabi(
            hesap_no=hesap_no,
            kullanici_id=current_user.id,
            yatirim_turu=yatirim_turu,
            toplam_bakiye=baslangic_tutar,
            kar_zarar=0.0,
            durum='Aktif'
        )
        
        db.session.add(yeni_yatirim)
        db.session.commit()
        
        flash(f'{yatirim_turu} yatırım hesabı başarıyla açıldı!', 'success')
        return redirect(url_for('investment'))
    
    hesaplar = Hesap.query.filter_by(kullanici_id=current_user.id).all()
    toplam_bakiye = sum([h.bakiye for h in hesaplar])
    return render_template('new_investment.html', toplam_bakiye=toplam_bakiye)

# Kart Detay
@app.route('/card/<int:kart_id>')
@login_required
def card_detail(kart_id):
    kart = Kart.query.get_or_404(kart_id)
    
    if kart.kullanici_id != current_user.id:
        flash('Bu karta erişim yetkiniz yok.', 'error')
        return redirect(url_for('cards'))
    
    return render_template('card_detail.html', kart=kart)

# Yatırım Hesabı Detay
@app.route('/investment/<int:yatirim_id>')
@login_required
def investment_detail(yatirim_id):
    yatirim = YatirimHesabi.query.get_or_404(yatirim_id)
    
    if yatirim.kullanici_id != current_user.id:
        flash('Bu yatırım hesabına erişim yetkiniz yok.', 'error')
        return redirect(url_for('investment'))
    
    return render_template('investment_detail.html', yatirim=yatirim)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

