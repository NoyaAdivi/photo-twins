<div dir="rtl">

<p align="center">
  <a href="https://github.com/NoyaAdivi/photo-twins"><img src="docs/readme/banner-he.svg" width="100%" alt="Photo Twins: מוצא תמונות כפולות, זהות ודומות"></a>
</p>

<p align="center"><a href="README.md"><img src="docs/readme/lang-en.svg" height="44" alt="Read in English"></a></p>

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/%D7%94%D7%AA%D7%97%D7%9C%D7%94_%D7%9E%D7%94%D7%99%D7%A8%D7%94-FFD5C9?style=for-the-badge&logo=rocket&logoColor=A8483A" alt="התחלה מהירה"></a>
  <a href="#how-it-works"><img src="https://img.shields.io/badge/%D7%90%D7%99%D7%9A_%D7%96%D7%94_%D7%A2%D7%95%D7%91%D7%93-DAD5FF?style=for-the-badge&logo=databricks&logoColor=5548C8" alt="איך זה עובד"></a>
  <a href="photo_twins.py"><img src="https://img.shields.io/badge/%D7%9C%D7%A7%D7%95%D7%93-D9F3E7?style=for-the-badge&logo=python&logoColor=1F7350" alt="לקוד"></a>
  <a href="https://github.com/NoyaAdivi/sort-photos"><img src="https://img.shields.io/badge/%D7%A4%D7%A8%D7%95%D7%99%D7%A7%D7%98_%D7%90%D7%97%3A_Sort_Photos-FBD5E0?style=for-the-badge&logo=github&logoColor=A03A5C" alt="פרויקט אח: Sort Photos"></a>
</p>

<p align="center">
  <a href="https://github.com/NoyaAdivi/photo-twins/actions/workflows/tests.yml"><img src="https://github.com/NoyaAdivi/photo-twins/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/NoyaAdivi/photo-twins?color=DAD5FF&labelColor=5548C8" alt="License"></a>
  <a href="https://github.com/NoyaAdivi/photo-twins/commits/main"><img src="https://img.shields.io/github/last-commit/NoyaAdivi/photo-twins?color=FFD5C9&labelColor=A8483A" alt="Last commit"></a>
  <a href="https://github.com/NoyaAdivi/photo-twins"><img src="https://img.shields.io/github/languages/top/NoyaAdivi/photo-twins?color=D9F3E7&labelColor=1F7350" alt="Top language"></a>
</p>

<h3 align="center">אותה תמונה שמורה בחמש תיקיות? מוצאים כל תאומה ומשאירים את הטובה ביותר.</h3>

<p align="center">
  Photo Twins סורק ספריית תמונות גדולה ומוצא <b>כפילויות זהות</b> (קבצים זהים לגמרי) ו<b>כפילויות דומות</b><br>(אותה תמונה אחרי הקטנה, דחיסה מחדש, שליחה בוואטסאפ או חיתוך קל). הוא אף פעם לא מוחק כלום.
</p>

<table align="center">
  <tr>
    <td align="center" width="25%"><a href="#how-it-works"><b>👯 2</b></a><br><sub>סוגי תאומות</sub></td>
    <td align="center" width="25%"><a href="#highlights"><b>🗑️ 0</b></a><br><sub>קבצים שנמחקים</sub></td>
    <td align="center" width="25%"><a href="#undo"><b>↩️ 1</b></a><br><sub>פקודה לביטול</sub></td>
    <td align="center" width="25%"><a href="#how-it-works"><b>🧬 64</b></a><br><sub>ביט טביעת אצבע לתמונה</sub></td>
  </tr>
</table>

<p align="center">
  <a href="#the-report"><img src="docs/readme/logo.svg" width="120" alt="הלוגו של Photo Twins"></a>
</p>

<a name="highlights"></a>
<p align="center"><a href="#how-it-works"><img src="docs/readme/highlights-he.svg" width="100%" alt="מה מיוחד בו"></a></p>

<table>
  <tr valign="top">
    <td width="33%"><p><b>🔍 מוצא גם את המוסתרות</b></p><ul><li><b>זהות:</b> קודם גודל קובץ, ואז SHA-256, כך שרק חשודות מקבלות hash</li><li><b>דומות:</b> hash תפיסתי של 64 ביט תופס עותקים מוקטנים, שנשמרו מחדש או נחתכו</li><li><b>מכיר סיבוב:</b> כיוון ה־EXIF מוחל קודם</li></ul></td>
    <td width="33%"><p><b>🛡️ בטוח מהיסוד</b></p><ul><li><b>רק דוח</b> כברירת מחדל, שום דבר לא זז</li><li><b>לא מוחק אף פעם:</b> העותקים העודפים עוברים לתיקייה שתבחרי</li><li><b>ביטול מלא:</b> כל העברה נרשמת ב־<code>moves.csv</code></li></ul></td>
    <td width="33%"><p><b>🏆 משאיר את העותק הטוב</b></p><ul><li><b>הכי הרבה פיקסלים</b> קודם, אחר כך הקובץ הגדול, ואז הישן</li><li><b>דוח ויזואלי</b> עם תמונות ממוזערות של כל קבוצה</li><li><b>מהיר:</b> חיפוש בעץ BK במקום להשוות כל זוג</li></ul></td>
  </tr>
</table>

<a name="how-it-works"></a>
<p align="center"><a href="#the-report"><img src="docs/readme/how-it-works-he.svg" width="100%" alt="איך זה עובד"></a></p>

```mermaid
flowchart LR
  A([📂 תיקיית התמונות]) --> B{אותו גודל קובץ?}
  B -->|כן| C[SHA-256]
  C --> D([👯 תאומות זהות])
  A --> E[סיבוב לפי EXIF<br/>9x8 אפור]
  E --> F[dHash<br/>טביעת אצבע 64 ביט]
  F --> G[חיפוש בעץ BK<br/>מרחק האמינג ≤ 6]
  G --> H([🪞 תאומות דומות])
  D --> K{בחירת העותק שנשאר<br/>הכי הרבה פיקסלים}
  H --> K
  K --> R([📊 report.html<br/>duplicates.csv])
  K -.->|--move-to| M([📦 Duplicates/<br/>moves.csv])
  style A fill:#E8E4FF,stroke:#6F60F0,color:#2C2668
  style D fill:#D9F3E7,stroke:#1F7350,color:#1F4D38
  style H fill:#DAD5FF,stroke:#5548C8,color:#2C2668
  style R fill:#FFE6DE,stroke:#E36E57,color:#2C2668
  style M fill:#FFF1C9,stroke:#B98A1E,color:#5C4410
```

<details open>
<summary><b>🧬 ה־hash התפיסתי, בדקה אחת</b></summary>

כל תמונה מוקטנת ל־9x8 פיקסלים אפורים, וכל פיקסל מושווה לשכן שמימינו: בהיר יותר זה `1`, כהה יותר זה `0`. כך מתקבלת טביעת אצבע של 64 ביט, שכמעט לא משתנה כשמקטינים תמונה, דוחסים אותה מחדש או מוסיפים פילטר עדין. שתי תמונות הן תאומות כשטביעות האצבע שלהן שונות בעד `--distance` ביטים (מרחק האמינג, 6 כברירת מחדל).

השוואה של כל זוג הייתה לוקחת *n²* צעדים (800 מיליון עבור 40,000 תמונות). **עץ BK** משתמש באי־שוויון המשולש כדי לדלג על ענפים שלמים, כך שכל חיפוש נוגע רק בחלק קטן מהספרייה. הקבוצות נבנות סביב העותק הטוב ביותר, כך ש־A דומה ל־B ו־B דומה ל־C לא מתחברים לקבוצה אחת כש־A ו־C שונות.
</details>

<a name="the-report"></a>
<p align="center"><a href="#quick-start"><img src="docs/readme/report-he.svg" width="100%" alt="הדוח"></a></p>

<p align="center">
  <a href="#quick-start"><img src="docs/readme/showcase.png" width="100%" alt="הדוח של Photo Twins: קבוצות של תמונות כפולות, והעותק שנשאר מסומן"></a>
</p>

<details open>
<summary><b>📁 מה נוצר</b></summary>

<div dir="ltr">

```
twins-report/
├── report.html      open it in any browser: thumbnails, sizes and paths of every group
└── duplicates.csv   one row per file: group, kind, keep/duplicate, size, resolution, distance

Duplicates/          only with --move-to, the original sub-folder structure is kept
└── moves.csv        the undo log
```
</div>

`report.html` נפתח בכל דפדפן ומראה כל קבוצה עם תמונות ממוזערות. `duplicates.csv` מכיל שורה לכל קובץ. התיקייה `Duplicates` נוצרת רק עם `--move-to`, ומבנה התיקיות המקורי נשמר בה.
</details>

<a name="tech-stack"></a>
<p align="center"><a href="#quick-start"><img src="docs/readme/tech-stack-he.svg" width="100%" alt="טכנולוגיות"></a></p>

<p align="center">
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-CFE6FA?style=for-the-badge&logo=python&logoColor=3F6D9F" alt="Python"></a>
  <a href="https://python-pillow.org"><img src="https://img.shields.io/badge/Pillow-D9F3E7?style=for-the-badge&logo=python&logoColor=1F7350" alt="Pillow"></a>
  <a href="https://github.com/bigcat88/pillow_heif"><img src="https://img.shields.io/badge/pillow--heif-FFD5C9?style=for-the-badge&logo=apple&logoColor=A8483A" alt="pillow-heif"></a>
  <a href="https://docs.pytest.org"><img src="https://img.shields.io/badge/pytest-DAD5FF?style=for-the-badge&logo=pytest&logoColor=5548C8" alt="pytest"></a>
  <a href="https://github.com/features/actions"><img src="https://img.shields.io/badge/GitHub_Actions-FBD5E0?style=for-the-badge&logo=githubactions&logoColor=A03A5C" alt="GitHub Actions"></a>
</p>

<a name="quick-start"></a>
<p align="center"><a href="#contact"><img src="docs/readme/quick-start-he.svg" width="100%" alt="התחלה מהירה"></a></p>

צריך **Python 3.10 ומעלה**. בלי הורדת מודל ובלי כרטיס מסך.

```bash
pip install -r requirements.txt
```

1. **סריקה ודוח** (שום דבר לא זז):
   ```bash
   python photo_twins.py "D:\Pictures" --similar
   ```
2. **פותחים** את `twins-report\report.html` ובודקים את הקבוצות.
3. **מעבירים את העותקים העודפים** לתיקייה נפרדת:
   ```bash
   python photo_twins.py "D:\Pictures" --similar --move-to "D:\Duplicates"
   ```
4. עוברים על `D:\Duplicates`, וכשהכול נראה טוב, מוחקים אותה בעצמך.

<a name="undo"></a>
> [!TIP]
> **התחרטת?** פקודה אחת מחזירה כל קובץ למקום שלו:
> ```bash
> python photo_twins.py --undo "D:\Duplicates\moves.csv"
> ```

> [!NOTE]
> עובד מצוין אחרי [Sort Photos](https://github.com/NoyaAdivi/sort-photos): קודם ממיינים, ואז מריצים את Photo Twins על `Sorted\photos`.

<details>
<summary><b>⚙️ כל האפשרויות</b></summary>

| אפשרות | תיאור |
| --- | --- |
| `--similar` | מוצא גם כפילויות דומות (מוקטנות, שנשמרו מחדש, מסובבות, חתוכות קלות) |
| `--distance N` | מרחק האמינג המקסימלי ל"דומות", 0 עד 64 (ברירת מחדל `6`). נמוך יותר זה מחמיר יותר |
| `--report DIR` | לאן לכתוב את `report.html` ואת `duplicates.csv` (ברירת מחדל `twins-report`) |
| `--move-to DIR` | מעביר לכאן את העותקים העודפים ורושם כל העברה |
| `--undo MOVES_CSV` | מחזיר כל קובץ שרשום ב־`moves.csv` |
| `--max-groups N` | כמה קבוצות יוצגו ב־`report.html` (ברירת מחדל `500`). ב־CSV תמיד יש את כולן |
| `--workers N` | כמה תהליכונים קוראים קבצים (ברירת מחדל: מספר הליבות) |
</details>

<details>
<summary><b>🧪 הרצת הבדיקות</b></summary>

```bash
pip install -r requirements-dev.txt
pytest -q
```
הבדיקות בונות ספריות תמונות קטנות תוך כדי ריצה ובודקות את ה־hash, את עץ ה־BK מול חיפוש מלא, קיבוץ של זהות ודומות, בחירת העותק שנשאר, והעברה וביטול מלאים. הן רצות על Windows ועל Ubuntu ב־[GitHub Actions](.github/workflows/tests.yml).
</details>

<details>
<summary><b>🖼️ פורמטים</b></summary>

JPG, PNG, BMP, WEBP, TIFF, GIF ו־HEIC/HEIF (דרך `pillow-heif`). קבצים שלא נקראים מדולגים ואף פעם לא מועברים.
</details>

<a name="contact"></a>
<p align="center"><a href="https://www.linkedin.com/in/noya-adivi/"><img src="docs/readme/footer-he.svg" width="100%" alt="נבנה על ידי נויה אדיבי"></a></p>

<p align="center">
  <a href="https://github.com/NoyaAdivi/photo-twins"><img src="https://img.shields.io/badge/%D7%9C%D7%A4%D7%A8%D7%95%D7%99%D7%A7%D7%98-FFD5C9?style=for-the-badge&logo=github&logoColor=A8483A" alt="לפרויקט"></a>
  <a href="https://www.linkedin.com/in/noya-adivi/"><img src="https://img.shields.io/badge/LinkedIn-DAD5FF?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0iIzU1NDhDOCIgZD0iTTIwLjQ1IDIwLjQ1aC0zLjU2di01LjU3YzAtMS4zMy0uMDMtMy4wNC0xLjg1LTMuMDQtMS44NiAwLTIuMTQgMS40NS0yLjE0IDIuOTR2NS42N0g5LjM1VjloMy40MXYxLjU2aC4wNWMuNDgtLjkgMS42NC0xLjg1IDMuMzctMS44NSAzLjYgMCA0LjI3IDIuMzcgNC4yNyA1LjQ2djYuMjh6TTUuMzQgNy40M2EyLjA2IDIuMDYgMCAxIDEgMC00LjEzIDIuMDYgMi4wNiAwIDAgMSAwIDQuMTN6TTcuMTIgMjAuNDVIMy41NlY5aDMuNTZ2MTEuNDV6TTIyLjIyIDBIMS43N0MuNzkgMCAwIC43NyAwIDEuNzN2MjAuNTRDMCAyMy4yMy43OSAyNCAxLjc3IDI0aDIwLjQ1Yy45OCAwIDEuNzgtLjc3IDEuNzgtMS43M1YxLjczQzI0IC43NyAyMy4yIDAgMjIuMjIgMHoiLz48L3N2Zz4=" alt="LinkedIn"></a>
  <a href="https://noyaadivi.github.io/noya-website"><img src="https://img.shields.io/badge/%D7%AA%D7%99%D7%A7_%D7%A2%D7%91%D7%95%D7%93%D7%95%D7%AA-D9F3E7?style=for-the-badge&logo=githubpages&logoColor=1F7350" alt="תיק עבודות"></a>
  <a href="https://github.com/NoyaAdivi"><img src="https://img.shields.io/badge/%D7%A2%D7%95%D7%93_%D7%A4%D7%A8%D7%95%D7%99%D7%A7%D7%98%D7%99%D7%9D-FBD5E0?style=for-the-badge&logo=github&logoColor=A03A5C" alt="עוד פרויקטים"></a>
</p>

</div>
