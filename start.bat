@echo off
REM ============================================
REM BetikBank Hızlı Başlatma Scripti
REM ============================================
echo.
echo ========================================
echo    BetikBank Uygulaması Başlatılıyor
echo ========================================
echo.

REM Python'un yüklü olup olmadığını kontrol et
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadı!
    echo Lutfen Python'u yukleyin: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python bulundu
python --version

REM Sanal ortam klasörünü kontrol et
if not exist "venv" (
    echo.
    echo [BILGI] Sanal ortam bulunamadi, olusturuluyor...
    python -m venv venv
    if errorlevel 1 (
        echo [HATA] Sanal ortam olusturulamadi!
        pause
        exit /b 1
    )
    echo [OK] Sanal ortam olusturuldu
) else (
    echo [OK] Sanal ortam mevcut
)

REM Sanal ortamı aktif et
echo.
echo [BILGI] Sanal ortam aktif ediliyor...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [HATA] Sanal ortam aktif edilemedi!
    pause
    exit /b 1
)

REM Pip'i güncelle
echo.
echo [BILGI] Pip guncelleniyor...
python -m pip install --upgrade pip --quiet

REM Gerekli paketleri yükle
echo.
echo [BILGI] Gerekli paketler yukleniyor...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [HATA] Paketler yuklenemedi!
    pause
    exit /b 1
)
echo [OK] Paketler yuklendi

REM Veritabanı klasörünü kontrol et
if not exist "instance" (
    echo.
    echo [BILGI] Instance klasoru olusturuluyor...
    mkdir instance
)

REM Uygulamayı başlat
echo.
echo ========================================
echo    Uygulama Baslatiliyor...
echo    Tarayicida acin: http://localhost:5000
echo ========================================
echo.
echo [BILGI] Durdurmak icin Ctrl+C basin
echo.

REM Flask uygulamasını çalıştır
python app.py

REM Uygulama kapatıldığında
echo.
echo [BILGI] Uygulama kapatildi.
pause

