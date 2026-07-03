# Mazka - Python Hosting Platform

منصة استضافة مشاريع بايثون تتيح للمستخدمين إنشاء وتشغيل مشاريعهم البرمجية مباشرة من المتصفح.

## المميزات

- إنشاء وإدارة المشاريع البرمجية
- تشغيل الكود المباشر
- محرر كود متقدم
- دعم لتثبيت الحزم باستخدام pip
- نظام مصادقة قوي
- دعم لتسجيل الدخول عبر Google و GitHub
- لوحة تحكم إدارية

## المتطلبات

- Python 3.11.9 أو أحدث
- pip

## التثبيت والتشغيل

1. استنسخ المستودع:
```bash
git clone https://github.com/yourusername/mazka.git
cd mazka
```

2. أنشئ ملف .env بناءً على .env.example:
```bash
cp .env.example .env
```

3. قم بتعديل إعدادات .env حسب بيئتك:
```bash
# للتطوير
DEBUG=true
ENVIRONMENT=development
DATABASE_URL=sqlite:///database.db

# للإنتاج
DEBUG=false
ENVIRONMENT=production
DATABASE_URL=postgresql://username:password@host:port/database_name
```

4. قم بتثبيت المكتبات المطلوبة:
```bash
pip install -r requirements.txt
```

5. قم بتشغيل التطبيق:
```bash
python main.py
```

6. افتح المتصفح على الرابط http://localhost:8000

## النشر

### النشر على Render

1. أنشئ حسابًا على [Render](https://render.com)
2. أنشئ تطبيقًا جديدًا من نوع Web Service
3. ربط المستودع الخاص بك
4. أضف المتغيرات البيئية في إعدادات التطبيق:
   - SECRET_KEY
   - DATABASE_URL (PostgreSQL)
   - DEBUG=false
   - ENVIRONMENT=production
5. اضغط على Deploy

### النشر يدويًا

1. قم بتعيين المتغيرات البيئية:
```bash
export SECRET_KEY="your-secret-key"
export DEBUG=false
export ENVIRONMENT=production
export DATABASE_URL="postgresql://username:password@host:port/database_name"
```

2. قم بتشغيل التطبيق باستخدام uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
```

## المتغيرات البيئية

| المتغير | الوصف | القيمة الافتراضية |
|---------|-------|----------------|
| SECRET_KEY | مفتاح سري لتوقيع التوكنات | super-secret-key-change-in-production-2025 |
| DEBUG | وضع التصحيح | true |
| ENVIRONMENT | بيئة التشغيل | development |
| DATABASE_URL | رابط قاعدة البيانات | sqlite:///database.db |
| SMTP_HOST | خادم SMTP | smtp.gmail.com |
| SMTP_PORT | منفذ SMTP | 587 |
| SMTP_USER | اسم مستخدم SMTP | - |
| SMTP_PASS | كلمة مرور SMTP | - |
| SMTP_FROM | عنوان البريد الإلكتروني | - |
| GOOGLE_CLIENT_ID | معرّف عميل Google | - |
| GOOGLE_CLIENT_SECRET | سر عميل Google | - |
| GITHUB_CLIENT_ID | معرّف عميل GitHub | - |
| GITHUB_CLIENT_SECRET | سر عميل GitHub | - |
| ADMIN_EMAIL | بريد الإدارة | admin@admin.com |

## الهيكل

- `main.py`: الكود الرئيسي للتطبيق
- `config.py`: إعدادات التطبيق
- `templates/`: قوالب HTML
- `static/`: ملفات CSS و JavaScript

## المشاكل الشائعة

### مشكلة bcrypt

تأكد من استخدام إصدار passlib المتوافق:
```bash
pip install passlib[bcrypt]>=1.7.4
```

### مشكلة قاعدة البيانات

تأكد من أن قاعدة البيانات تعمل بشكل صحيح:
```bash
# للتأكد من وجود الجداول
python -c "from main import engine; from main import Base; Base.metadata.create_all(bind=engine)"
```

## المساهمة

1. Fork المستودع
2. أنشئ فرعًا جديدًا (git checkout -b feature/amazing-feature)
3. قم بالcommit للتغييرات (git commit -m 'Add some amazing feature')
4. قم بالpush إلى الفرع (git push origin feature/amazing-feature)
5. افتح Pull Request

## الترخيص

هذا المشروع مرخص بموجب MIT - انظر ملف LICENSE للحصول على التفاصيل.
