# ROS Official Package & Kernel Repository (`misaaca/ros-pkg`)

مخزن رسمی بسته‌ها و آپدیت کرنل سیستم‌عامل **ROS** (متصل به دستورهای `apt update`، `apt upgrade` و `apt install`).

## ساختار پوشه‌ها

```text
ros-pkg/
├── kernel/                  # آخرین فایل باینری کرنل (ros_kernel-v0.3.43-rumi)
├── packages/                # بسته‌های باینری قابل نصب با فرمت .rop
├── tools/
│   ├── build_rop.py         # ساخت بسته جدید .rop با چک‌سام SHA-256
│   ├── update_index.py      # تولید خودکار Packages.toml / Packages.json / Packages.gz / kernel.toml
│   └── verify_repo.py       # بررسی سلامت تمام بسته‌ها و کرنل
├── Packages.toml            # فهرست اصلی که `apt update` از گیت‌هاب می‌خواند
├── Packages.json            # نسخه JSON فهرست
├── Packages.gz              # نسخه فشرده فهرست
├── kernel.toml              # اطلاعات آخرین بیلد کرنل (version + build + sha256)
└── SHA256SUMS               # چک‌سام فایل‌ها
```

## انتشار آپدیت جدید کرنل (فقط با یک دستور)

این ریپازیتوری را کنار پوشه سورس `ROS` کلون کنید (`../ros-pkg`):

```bash
git clone https://github.com/misaaca/ros-pkg.git ../ros-pkg
```

سپس از داخل پوشه `ROS` اجرا کنید:

```bash
# بیلد کرنل جدید، کپی به ../ros-pkg/kernel/، تولید ایندکس با build_hex و SHA-256، و کامیت لوکال:
./scripts/publish_to_repo.sh --build

# سپس خودتان پوش کنید روی گیت‌هاب (یا مستقیم با --push):
cd ../ros-pkg && git push origin main
```

> حتی اگر شماره نسخه روی `0.3.43` ثابت بماند، تغییر `build` (هش ۸ کاراکتری) و `sha256` در `Packages.toml` باعث می‌شود کاربران با اجرای `apt update && apt upgrade` آخرین نسخه کرنل را دریافت و مستقیم روی پارتیشن بوت دیسک نصب‌شده جایگزین کنند (بدون نیاز به نصب مجدد سیستم‌عامل).

## اضافه کردن بسته جدید برای `apt install <name>`

```bash
python3 tools/build_rop.py \
  --name mytool \
  --version 1.0.0 \
  --description "My custom ROS tool" \
  --file /usr/local/bin/mytool:0755:./mytool.sh \
  --output packages/mytool-1.0.0.rop

python3 tools/update_index.py
python3 tools/verify_repo.py
git add -A && git commit -m "pkg: add mytool 1.0.0" && git push origin main
```
