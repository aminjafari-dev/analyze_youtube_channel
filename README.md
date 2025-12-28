# YouTube Channel Analyzer

یک برنامه Python با رابط گرافیکی برای استخراج اطلاعات ویدیوهای Shorts از کانال‌های یوتیوب، دریافت transcript و ذخیره اطلاعات در فایل Excel.

## ویژگی‌ها

- 🎯 استخراج ویدیوهای Shorts از کانال‌های یوتیوب
- 📊 دریافت اطلاعات کامل ویدیوها (بازدید، لایک، کامنت، توضیحات)
- 📝 دریافت transcript ویدیوها از tubetranscript.com
- 💾 ذخیره اطلاعات در فایل Excel با فرمت `{channel_name}_{date}_{time}.xlsx`
- 🎨 رابط گرافیکی کاربرپسند و داینامیک
- ⚙️ قابلیت تنظیم تعداد ویدیوها (1-20)
- 🔄 انتخاب حالت مرتب‌سازی (Popular/Recent)
- 🔁 مدیریت خطا با قابلیت تلاش مجدد

## نیازمندی‌ها

- Python 3.8 یا بالاتر
- Google Chrome
- ChromeDriver (به صورت خودکار نصب می‌شود با webdriver-manager)

## نصب

1. کلون کردن یا دانلود پروژه:
```bash
cd analyze_youtube_channel
```

2. نصب وابستگی‌ها:
```bash
pip install -r requirements.txt
```

## استفاده

1. اجرای برنامه:
```bash
python src/main.py
```

2. در رابط گرافیکی:
   - آدرس کانال یوتیوب را وارد کنید (مثلاً: `https://www.youtube.com/@channelname`)
   - تعداد ویدیوها را انتخاب کنید (1-20)
   - حالت مرتب‌سازی را انتخاب کنید (Popular یا Recent)
   - روی دکمه "Start Analysis" کلیک کنید

3. برنامه به صورت خودکار:
   - به بخش Shorts کانال می‌رود
   - ویدیوها را بر اساس حالت انتخابی مرتب می‌کند
   - اطلاعات ویدیوها را استخراج می‌کند
   - transcript هر ویدیو را از tubetranscript.com دریافت می‌کند
   - همه اطلاعات را در یک فایل Excel ذخیره می‌کند

## ساختار پروژه

```
analyze_youtube_channel/
├── src/
│   ├── main.py                 # نقطه ورود اصلی
│   ├── gui/                    # کامپوننت‌های رابط گرافیکی
│   │   ├── main_window.py
│   │   ├── components.py
│   │   └── styles.py
│   ├── scrapers/               # ماژول‌های استخراج داده
│   │   ├── youtube_scraper.py
│   │   └── transcript_scraper.py
│   ├── data/                   # مدیریت داده
│   │   ├── excel_handler.py
│   │   └── models.py
│   ├── utils/                  # ابزارهای کمکی
│   │   ├── browser_manager.py
│   │   ├── config.py
│   │   └── validators.py
│   └── exceptions/             # استثناهای سفارشی
│       └── custom_exceptions.py
├── requirements.txt
└── README.md
```

## فرمت فایل Excel

فایل Excel شامل ستون‌های زیر است:
- Channel Name
- Video Title
- Video URL
- Upload Date
- Views
- Likes
- Comments
- Description
- Transcript

نام فایل به صورت `{channel_name}_{YYYY-MM-DD}_{HH-MM-SS}.xlsx` ذخیره می‌شود.

## نکات مهم

- برنامه از Selenium برای خودکارسازی مرورگر استفاده می‌کند
- مرورگر Chrome باید نصب باشد
- اتصال به اینترنت برای استخراج داده‌ها ضروری است
- دریافت transcript ممکن است چند ثانیه طول بکشد
- در صورت خطا، برنامه به صورت خودکار تلاش مجدد می‌کند

## عیب‌یابی

### مشکل: ChromeDriver پیدا نمی‌شود
- مطمئن شوید Chrome نصب است
- webdriver-manager به صورت خودکار ChromeDriver را مدیریت می‌کند

### مشکل: ویدیوها پیدا نمی‌شوند
- مطمئن شوید URL کانال صحیح است
- کانال باید ویدیوهای Shorts داشته باشد

### مشکل: Transcript دریافت نمی‌شود
- برخی ویدیوها ممکن است transcript نداشته باشند
- اتصال اینترنت را بررسی کنید
- tubetranscript.com ممکن است محدودیت داشته باشد

## مجوز

این پروژه برای استفاده آموزشی و شخصی است.

## نکات امنیتی

- این برنامه فقط برای استفاده شخصی و آموزشی طراحی شده است
- از قوانین و شرایط استفاده YouTube و tubetranscript.com پیروی کنید
- از استخراج داده‌ها به صورت انبوه خودداری کنید

