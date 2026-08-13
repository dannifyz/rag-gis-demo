# rag-gis-demo

ระบบ RAG (Retrieval-Augmented Generation) สำหรับถาม-ตอบเอกสารกฎหมายภาษาไทย (พ.ร.บ. / กฎกระทรวง / ประกาศกระทรวง) ในรูปแบบ PDF

- **Loader / Splitter**: LangChain + `pypdf`
- **Embeddings**: Google `models/gemini-embedding-001` (768 มิติ)
- **Vector store**: Chroma (persist ไว้ที่ `chroma_db/`)
- **LLM**: Google `gemini-2.5-flash`

---

## โครงสร้างโปรเจกต์

```
rag-gis-demo/
├── data/                      # PDF ต้นทาง (ไม่ commit ขึ้น git)
│   └── law/
│       ├── act/               # พระราชบัญญัติ
│       ├── min_notif/         # ประกาศกระทรวง
│       └── min_reg/           # กฎกระทรวง
├── chroma_db/                 # ฐานข้อมูล vector (สร้างอัตโนมัติ, ไม่ commit)
├── result/                    # ผลลัพธ์การ query แบบ .md (สร้างอัตโนมัติ, ไม่ commit)
├── src/rag_gis_demo/
│   ├── __init__.py            # โหลด .env + กำหนด PROJECT_ROOT
│   ├── vectorstore.py         # ตั้งค่า embeddings + Chroma
│   ├── ingest.py              # โหลด → ทำความสะอาด → ตัด chunk → เก็บลง DB
│   ├── query.py               # ค้นหา + ถาม LLM + บันทึกผลลัพธ์
│   ├── test_pdf.py            # เครื่องมือดูข้อความที่สกัดจาก PDF
│   └── main.py                # ทดสอบการเชื่อมต่อ LLM
├── pyproject.toml
└── .env                       # เก็บ GOOGLE_API_KEY (ไม่ commit)
```

---

## การติดตั้ง (Setup)

### 1. สิ่งที่ต้องมี

- **Python 3.14+** (กำหนดไว้ใน `.python-version`)
- **[uv](https://docs.astral.sh/uv/)** — ตัวจัดการ dependency และ virtual environment ของโปรเจกต์นี้

ติดตั้ง `uv` บน Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone และติดตั้ง dependency

```powershell
git clone <repo-url>
cd rag-gis-demo
uv sync
```

`uv sync` จะสร้าง `.venv/` ให้อัตโนมัติ ติดตั้ง dependency ทั้งหมดจาก `uv.lock` และติดตั้งตัวโปรเจกต์เองในโหมด editable (ทำให้เรียก command ใน `[project.scripts]` ได้)

ถ้าต้องการเครื่องมือ dev (ruff) ด้วย:

```powershell
uv sync --group dev
```

### 3. ตั้งค่า API key

โปรเจกต์ต้องใช้ Google Gemini API key ทั้งตอน ingest (embeddings) และตอน query (LLM)

```
GOOGLE_API_KEY=your-api-key-here
```

> ถ้าไม่ได้ตั้งค่า key ทุกคำสั่งจะขึ้น error `RuntimeError: GOOGLE_API_KEY not set.` ตั้งแต่ตอน import

### 4. เตรียมไฟล์ PDF

วางไฟล์ PDF ไว้ใต้ `data/` (ค้นหาแบบ recursive ด้วย glob `**/*.pdf` จึงจัดโฟลเดอร์ย่อยได้ตามต้องการ) โฟลเดอร์ `data/` ไม่ถูก commit ขึ้น git ดังนั้นต้องเตรียมเอง

โครงสร้างที่ใช้อยู่ปัจจุบัน:

| โฟลเดอร์ | เนื้อหา |
| --- | --- |
| `data/law/act/` | พระราชบัญญัติ |
| `data/law/min_reg/` | กฎกระทรวง |
| `data/law/min_notif/` | ประกาศกระทรวง |

---

## คำสั่งที่ใช้งานได้

คำสั่งทั้งหมดประกาศไว้ใน `[project.scripts]` ของ `pyproject.toml` เรียกผ่าน `uv run <ชื่อคำสั่ง>` ได้เลย

| คำสั่ง | Entry point | หน้าที่ |
| --- | --- | --- |
| `rag-gis-demo` | `rag_gis_demo.main:main` | ทดสอบว่าเชื่อมต่อ LLM ได้ |
| `rag-gis-ingest` | `rag_gis_demo.ingest:main` | นำ PDF เข้าสู่ vector store |
| `rag-gis-query` | `rag_gis_demo.query:main` | ถามคำถามกับเอกสาร |
| `rag-gis-test-pdf` | `rag_gis_demo.test_pdf:main` | ดูข้อความที่สกัดได้จาก PDF ทีละไฟล์ |

### `rag-gis-demo` — ทดสอบการเชื่อมต่อ

ส่งข้อความ `"สวัสดีครับ!"` ไปหา `gemini-2.5-flash` แล้วพิมพ์คำตอบออกมา ใช้เช็กว่า API key ใช้งานได้จริง

```powershell
uv run rag-gis-demo
```

### `rag-gis-ingest` — นำเอกสารเข้า vector store

ขั้นตอนที่ทำ: โหลด PDF ทุกไฟล์ใต้ `data/` → normalize ตัวอักษรไทย (แปลง glyph ใน Private Use Area กลับเป็นสระ/วรรณยุกต์จริง) → ลบลายน้ำ "สำนักงานคณะกรรมการกฤษฎีกา" → ตัดเป็น chunk ขนาด 800 ตัวอักษร (overlap 80) → ใส่ id รูปแบบ `{source}:{page}:{index}` → เก็บลง Chroma

```powershell
# เพิ่มเอกสารใหม่เข้า DB (ข้าม chunk ที่มีอยู่แล้ว)
uv run rag-gis-ingest

# ล้าง collection ทิ้งแล้ว ingest ใหม่ทั้งหมด
uv run rag-gis-ingest --reset
```

| Argument | ค่าเริ่มต้น | ความหมาย |
| --- | --- | --- |
| `--reset` | ปิด | ล้าง collection เดิมก่อนเริ่ม ingest |

เนื่องจากใช้ id เป็นตัวเช็ก การรันซ้ำโดยไม่ใส่ `--reset` จึงปลอดภัย — เพิ่มเฉพาะ chunk ที่ยังไม่มีใน DB (จะขึ้นข้อความ `No new documents to add` ถ้าไม่มีอะไรใหม่)

> ⚠️ ขั้นตอนนี้เรียก embedding API ทุก chunk ถ้ามีเอกสารเยอะจะใช้เวลาและโควตาพอสมควร ควรใช้ `--reset` เมื่อจำเป็นจริง ๆ เท่านั้น

### `rag-gis-query` — ถามคำถาม

ค้นหา chunk ที่ใกล้เคียงที่สุดจาก Chroma แล้วส่งเป็นบริบทให้ LLM ตอบ โดยบังคับให้ตอบจากบริบทเท่านั้น (ถ้าไม่มีข้อมูลจะตอบว่า "ไม่พบข้อมูลในเอกสาร")

```powershell
uv run rag-gis-query "การขออนุญาตก่อสร้างอาคารต้องยื่นเอกสารอะไรบ้าง"

# ปรับจำนวน chunk ที่ดึงมาเป็นบริบท
uv run rag-gis-query "นิยามของคำว่าอาคาร" -k 10
```

| Argument | ค่าเริ่มต้น | ความหมาย |
| --- | --- | --- |
| `query_text` | (จำเป็น) | คำถาม — ถ้ามีเว้นวรรคต้องครอบด้วย `"` |
| `-k` | `5` | จำนวน chunk ที่ดึงมาเป็นบริบท |

ผลลัพธ์จะพิมพ์ออกหน้าจอ พร้อมบันทึกเป็นไฟล์ `result/yyyymmdd-hhmmss-result.md` ซึ่งมีหัวข้อ คำถาม / คำตอบ / อ้างอิง โดยส่วนอ้างอิงระบุเป็นชื่อไฟล์ + เลขหน้า เช่น `[1] law/act/law_001.pdf (หน้า 7)`

> ต้องรัน `rag-gis-ingest` ก่อนอย่างน้อยหนึ่งครั้ง มิฉะนั้นจะไม่มีข้อมูลใน DB ให้ค้นหา

### `rag-gis-test-pdf` — ตรวจข้อความที่สกัดจาก PDF

ใช้ตรวจว่า pipeline ทำความสะอาดข้อความไทยได้ถูกต้องหรือยัง ก่อนจะ ingest จริง คำสั่งนี้ไม่แตะ vector store และไม่เรียก API

```powershell
# ใช้ไฟล์ default (law/min_reg/MR_No_001.pdf)
uv run rag-gis-test-pdf

# ระบุไฟล์เอง (path สัมพัทธ์กับ data/)
uv run rag-gis-test-pdf law/act/law_001.pdf

# ดูข้อความดิบก่อนทำความสะอาด เพื่อเทียบผลลัพธ์
uv run rag-gis-test-pdf law/act/law_001.pdf --raw

# ดูเฉพาะหน้าที่ต้องการ (เลขหน้าเริ่มที่ 0 ตาม metadata)
uv run rag-gis-test-pdf law/act/law_001.pdf --page 3
```

| Argument | ค่าเริ่มต้น | ความหมาย |
| --- | --- | --- |
| `pdf` | `law/min_reg/MR_No_001.pdf` | path ของ PDF สัมพัทธ์กับ `data/` |
| `--raw` | ปิด | ข้ามขั้นตอน normalize / ลบลายน้ำ |
| `--page` | ทุกหน้า | พิมพ์เฉพาะหน้านี้ (0-based) |

---

## Workflow ทั่วไป

```powershell
uv sync                                    # 1. ติดตั้ง dependency
Copy-Item .env.example .env                # 2. ใส่ GOOGLE_API_KEY ใน .env
uv run rag-gis-demo                        # 3. เช็กว่าเชื่อมต่อ LLM ได้
uv run rag-gis-test-pdf                    # 4. เช็กว่าอ่าน PDF ออกถูกต้อง
uv run rag-gis-ingest                      # 5. นำเอกสารเข้า DB
uv run rag-gis-query "คำถามของคุณ"          # 6. ถามคำถาม
```

---

## การพัฒนา

```powershell
# ตรวจ lint
uv run ruff check .

# แก้ปัญหา lint อัตโนมัติ
uv run ruff check --fix .

# จัดรูปแบบโค้ด
uv run ruff format .
```

### จัดการ dependency

```powershell
uv add <package>                # เพิ่ม dependency หลัก
uv add --group dev <package>    # เพิ่ม dev dependency
uv remove <package>             # ลบ dependency
uv lock --upgrade               # อัปเดต uv.lock
```

### รันโมดูลโดยตรง

ทุกไฟล์มี `if __name__ == "__main__"` จึงเรียกแบบโมดูลได้เช่นกัน (ผลเหมือน `[project.scripts]`)

```powershell
uv run python -m rag_gis_demo.ingest --reset
uv run python -m rag_gis_demo.query "คำถามของคุณ"
```

---

## Troubleshooting

| อาการ | สาเหตุ / วิธีแก้ |
| --- | --- |
| `RuntimeError: GOOGLE_API_KEY not set.` | ยังไม่มีไฟล์ `.env` หรือยังไม่ได้ใส่ค่า key |
| ผล query เป็น "ไม่พบข้อมูลในเอกสาร" ตลอด | ยังไม่ได้รัน `rag-gis-ingest` หรือ `data/` ว่าง ลองเพิ่ม `-k` ให้มากขึ้น |
| ภาษาไทยเพี้ยน / วรรณยุกต์หาย | ตรวจด้วย `rag-gis-test-pdf --raw` เทียบกับแบบปกติ อาจต้องเพิ่ม mapping ใน `PUA_TO_THAI` ที่ `src/rag_gis_demo/ingest.py` |
| Console แสดงภาษาไทยไม่ได้ | `query.py` และ `test_pdf.py` ตั้ง stdout เป็น UTF-8 ให้แล้ว แต่ถ้ายังเพี้ยนให้รัน `chcp 65001` ก่อน |
| ผลลัพธ์ค้างเก่าหลังแก้ pipeline การ clean | รัน `uv run rag-gis-ingest --reset` เพื่อสร้าง embedding ใหม่ทั้งหมด |
