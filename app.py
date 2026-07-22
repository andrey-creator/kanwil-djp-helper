

import io
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
import plotly.express as px

# ====================================================================================
# 1. KONFIGURASI HALAMAN & CUSTOM CSS (TEMA NAVY BLUE & GOLD - KHAS INSTANSI)
# ====================================================================================

st.set_page_config(
    page_title="Generator Narasi Nota Dinas & LPP - Kanwil DJP",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY = "#003366"
GOLD = "#F4B400"
WHITE = "#FFFFFF"
LIGHT_BG = "#F5F7FA"
TEXT_DARK = "#1F2937"

CUSTOM_CSS = f"""
<style>

.stApp {{
    background-color: #f5f7fa;
}}

.main-container {{
    padding-top: 10px;
}}

.metric-card {{
    background:white;
    border-radius:12px;
    padding:18px;
    border-top:4px solid #F4B400;
    box-shadow:0 3px 10px rgba(0,0,0,.08);
}}

.stButton > button {{
    background:#003366;
    color:white;
    border:none;
    border-radius:8px;
    font-weight:600;
}}

.stButton > button:hover {{
    background:#004a8f;
}}

.metric-title {{
    font-size: 13px;
    color: #6b7280;
}}

.metric-value {{
    font-size: 28px;
    font-weight: 700;
    color: {NAVY};
}}

.document-preview {{
    width: 100%;
    max-width: 900px;
    margin:auto;
    background:white;
    padding:50px;
    border-radius:10px;
    box-shadow:0 0 20px rgba(0,0,0,.15);
    min-height:800px;
    white-space: pre-wrap;
    line-height:1.8;
    color:#222;
}}

.dashboard-card {{
    background:white;
    padding:20px;
    border-radius:12px;
    box-shadow:0 2px 8px rgba(0,0,0,.08);
}}

.sidebar-title {{
    color:white;
    font-size:18px;
    font-weight:700;
}}

section[data-testid="stSidebar"] {{
    background: linear-gradient(
        180deg,
        #003366 0%,
        #004080 100%
    );
}}

section[data-testid="stSidebar"] * {{
    color: white !important;
}}

.section-card {{
    background:white;
    border-radius:12px;
    padding:20px;
    margin-bottom:15px;
    border-left:4px solid #F4B400;
    box-shadow:0 2px 8px rgba(0,0,0,.08);
}}

.app-header{{
    display:flex;
    align-items:center;
    gap:16px;

    background:#003366;

    padding:20px;

    border-radius:12px;

    color:white;

    margin-bottom:20px;
}}

.header-logo{{
    display:flex;
    align-items:center;
    justify-content:center;
}}

</style>

"""
st.markdown("""
<div style="
background:#003366;
padding:20px;
border-radius:12px;
color:white;
margin-bottom:20px;
">
<h2 style="margin:0;">
Generator Narasi Nota Dinas & LPP
</h2>
<div style="opacity:.85;">
Kanwil Direktorat Jenderal Pajak
</div>
</div>
""", unsafe_allow_html=True)

# ====================================================================================
# 2. DATA REFERENSI / MASTER DATA (DUMMY / DEFAULT)
# ====================================================================================

DAFTAR_KPP = [
    "KPP Pratama Contoh Satu",
    "KPP Pratama Contoh Dua",
    "KPP Pratama Contoh Tiga",
    "KPP Madya Contoh",
    "KPP Pratama Contoh Empat",
    "KPP Pratama Contoh Lima",
]

JENIS_WP_LIST = ["Wajib Pajak Badan", "Wajib Pajak Orang Pribadi"]

JENIS_INDIKASI_LIST = [
    "Ekualisasi Omzet PPN vs PPh Badan",
    "Biaya Nondeductible",
    "Objek PPh Potput Belum Dipotong/Disetor",
    "Selisih Transfer Pricing (Transaksi Afiliasi)",
    "Selisih Laporan Keuangan vs SPT Tahunan",
    "Indikasi Faktur Pajak Tidak Sah/Fiktif",
    "Harta/Penghasilan Belum Dilaporkan (Data ILAP)",
    "Ketidaksesuaian Data Spasial/Properti dengan SPT",
]

SUMBER_DATA_LIST = [
    "Data Internal DJP",
    "Data ILAP (Instansi, Lembaga, Asosiasi, Pihak Lain)",
    "Hasil Sanding Data Spasial",
    "Laporan Keuangan Audit",
    "Hasil Konfirmasi Faktur Pajak",
    "Data Perbankan/PPATK",
    "Data e-Commerce/Marketplace",
]

JENIS_PAJAK_LIST = [
    "PPh Badan",
    "PPN",
    "PPh Pasal 21",
    "PPh Pasal 23",
    "PPh Pasal 26",
    "PPh Final",
]

TINDAK_LANJUT_LIST = [
    "Penerbitan Surat Permintaan Penjelasan atas Data dan/atau Keterangan (SP2DK)",
    "Imbauan Pembetulan SPT",
    "Konseling Tatap Muka",
    "Pengusulan Pemeriksaan Khusus/Spesifik",
    "Usulan Pemeriksaan Bukti Permulaan (Bukper)",
]

TAHUN_PAJAK_LIST = [str(y) for y in range(date.today().year, date.today().year - 6, -1)]

DASAR_HUKUM_DEFAULT = (
    "Surat Edaran Direktur Jenderal Pajak Nomor SE-05/PJ/2022 tentang Pengawasan "
    "Kepatuhan Wajib Pajak, serta ketentuan peraturan perundang-undangan perpajakan "
    "yang berlaku"
)

# ====================================================================================
# 3. FUNGSI UTILITAS
# ====================================================================================

def format_rupiah(nilai: float) -> str:
    """Mengubah nilai numerik menjadi format mata uang Rupiah Indonesia.

    Contoh: 1250000000 -> 'Rp 1.250.000.000,00'
    """
    try:
        nilai = float(nilai)
    except (TypeError, ValueError):
        nilai = 0.0
    bagian_bulat = int(nilai)
    bagian_desimal = round((nilai - bagian_bulat) * 100)
    bulat_str = f"{bagian_bulat:,}".replace(",", ".")
    return f"Rp {bulat_str},{bagian_desimal:02d}"


def _terbilang_angka(n: int) -> str:
    """Fungsi rekursif pengubah angka menjadi ejaan terbilang Bahasa Indonesia.

    Mendukung nilai hingga triliunan. Digunakan secara internal oleh
    fungsi `terbilang`.
    """
    satuan = [
        "", "satu", "dua", "tiga", "empat", "lima",
        "enam", "tujuh", "delapan", "sembilan", "sepuluh",
        "sebelas",
    ]

    if n < 0:
        return "minus " + _terbilang_angka(-n)
    if n < 12:
        return satuan[n]
    if n < 20:
        return _terbilang_angka(n - 10) + " belas"
    if n < 100:
        return _terbilang_angka(n // 10) + " puluh " + _terbilang_angka(n % 10)
    if n < 200:
        return "seratus " + _terbilang_angka(n - 100)
    if n < 1000:
        return _terbilang_angka(n // 100) + " ratus " + _terbilang_angka(n % 100)
    if n < 2000:
        return "seribu " + _terbilang_angka(n - 1000)
    if n < 1_000_000:
        return _terbilang_angka(n // 1000) + " ribu " + _terbilang_angka(n % 1000)
    if n < 1_000_000_000:
        return _terbilang_angka(n // 1_000_000) + " juta " + _terbilang_angka(n % 1_000_000)
    if n < 1_000_000_000_000:
        return (
            _terbilang_angka(n // 1_000_000_000)
            + " miliar "
            + _terbilang_angka(n % 1_000_000_000)
        )
    return (
        _terbilang_angka(n // 1_000_000_000_000)
        + " triliun "
        + _terbilang_angka(n % 1_000_000_000_000)
    )


def terbilang(nilai: float) -> str:
    """Mengubah nilai nominal Rupiah menjadi kalimat ejaan terbilang.

    Contoh: 1250000000 -> 'satu miliar dua ratus lima puluh juta rupiah'
    """
    try:
        nilai = int(round(float(nilai)))
    except (TypeError, ValueError):
        nilai = 0
    if nilai == 0:
        return "nol rupiah"
    hasil = _terbilang_angka(nilai).strip()
    # Rapikan spasi ganda yang mungkin muncul dari proses rekursif
    hasil = " ".join(hasil.split())
    return f"{hasil} rupiah"


def format_npwp(npwp_raw: str) -> str:
    """Merapikan format NPWP secara otomatis berdasarkan jumlah digit.

    - 15 digit (format lama): XX.XXX.XXX.X-XXX.XXX
    - 16 digit (format baru / NIK): XXXX.XXXX.XXXX.XXXX
    Karakter selain angka akan dibuang terlebih dahulu sebelum diformat ulang.
    """
    digits = "".join(ch for ch in str(npwp_raw) if ch.isdigit())
    if len(digits) == 15:
        return (
            f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}.{digits[8:9]}-"
            f"{digits[9:12]}.{digits[12:15]}"
        )
    if len(digits) == 16:
        return f"{digits[0:4]}.{digits[4:8]}.{digits[8:12]}.{digits[12:16]}"
    # Jika jumlah digit tidak sesuai standar, kembalikan apa adanya
    return npwp_raw


def hitung_tanggal_batas(hari_kerja: int) -> str:
    """Menghitung estimasi tanggal batas waktu respon berdasarkan jumlah hari
    kerja (Senin-Jumat) sejak hari ini, lalu mengembalikannya dalam format
    tanggal Indonesia (dd Bulan yyyy).
    """
    nama_bulan = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]
    hasil = date.today()
    sisa = int(hari_kerja)
    while sisa > 0:
        hasil += timedelta(days=1)
        if hasil.weekday() < 5:  # 0-4 = Senin-Jumat
            sisa -= 1
    return f"{hasil.day} {nama_bulan[hasil.month]} {hasil.year}"


def tanggal_indonesia(tgl: date) -> str:
    """Mengembalikan representasi tanggal dalam Bahasa Indonesia."""
    nama_bulan = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]
    return f"{tgl.day} {nama_bulan[tgl.month]} {tgl.year}"


def buat_nomor_draf() -> str:
    """Membuat nomor draf otomatis berbasis timestamp saat generate dilakukan."""
    now = datetime.now()
    return f"ND-{now.strftime('%d%m%Y')}-{now.strftime('%H%M%S')}/PJ.KANWIL/{now.year}"


# ====================================================================================
# 4. TEMPLATE NARASI DEFAULT (DAPAT DIUBAH MELALUI MODUL 3)
# ====================================================================================

DEFAULT_TEMPLATE_PEMBUKA = """NOTA DINAS
Nomor        : {nomor_draf}
Tanggal      : {tanggal}
Kepada       : {kepada}
Dari         : {dari}
Hal          : {hal}

Sehubungan dengan pelaksanaan tugas pengawasan kepatuhan perpajakan pada {kpp}, \
bersama ini disampaikan hasil analisis dan rekomendasi tindak lanjut pengawasan \
terhadap Wajib Pajak sebagai berikut:"""

DEFAULT_TEMPLATE_ISI = """A. URAIAN LATAR BELAKANG DAN IDENTITAS WAJIB PAJAK
Berdasarkan hasil penelitian dan analisis yang dilakukan oleh {ar} selaku Account \
Representative/Tim Pengawas pada {kpp}, terhadap Wajib Pajak atas nama {nama_wp} \
dengan NPWP {npwp} yang berstatus sebagai {jenis_wp}, untuk Tahun/Masa Pajak {tahun_pajak}, \
ditemukan indikasi ketidakpatuhan perpajakan yang memerlukan tindak lanjut pengawasan.

B. TEMUAN INDIKASI KETIDAKPATUHAN DAN SUMBER DATA
Indikasi ketidakpatuhan yang teridentifikasi berupa {jenis_indikasi}. Analisis \
tersebut bersumber dari {sumber_data}. Uraian ringkas hasil penelitian dan analisis \
data/keterangan adalah sebagai berikut: {uraian_temuan}

C. ESTIMASI POTENSI KEWAJIBAN PERPAJAKAN
Berdasarkan hasil analisis sebagaimana dimaksud pada huruf B, diestimasikan \
terdapat potensi kewajiban perpajakan yang belum dilaporkan/dipenuhi sebesar \
{potensi_rupiah} ({potensi_terbilang}), yang terkait dengan jenis pajak: {jenis_pajak}."""

DEFAULT_TEMPLATE_PENUTUP = """D. REKOMENDASI DAN LANGKAH PENGAWASAN
Sehubungan dengan uraian tersebut di atas dan mengacu pada {dasar_hukum}, \
direkomendasikan untuk dilakukan tindak lanjut pengawasan berupa {tindak_lanjut} \
kepada Wajib Pajak yang bersangkutan, dengan batas waktu respon/penyelesaian \
paling lambat tanggal {batas_waktu} ({batas_hari} hari kerja sejak nota dinas ini \
diterbitkan).

Demikian nota dinas ini disampaikan untuk dapat ditindaklanjuti sebagaimana mestinya.

Hormat kami,
{dari}"""

# ====================================================================================
# 5. INISIALISASI SESSION STATE
# ====================================================================================

def init_session_state():
    """Menginisialisasi seluruh nilai default pada session_state Streamlit,
    baik untuk data form maupun template narasi yang dapat dikustomisasi.
    """
    defaults = {
        "tpl_pembuka": DEFAULT_TEMPLATE_PEMBUKA,
        "tpl_isi": DEFAULT_TEMPLATE_ISI,
        "tpl_penutup": DEFAULT_TEMPLATE_PENUTUP,
        "hasil_narasi_single": "",
        "hasil_batch_df": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()

# ====================================================================================
# 6. FUNGSI INTI PEMBUATAN NARASI
# ====================================================================================

def generate_narasi(data: dict) -> str:
    """Menyusun narasi Nota Dinas lengkap (pembuka + isi + penutup) berdasarkan
    template yang tersimpan pada session_state dan data input yang diberikan.

    Parameter
    ---------
    data : dict
        Kamus berisi seluruh placeholder yang dibutuhkan oleh template,
        misalnya nama_wp, npwp, kpp, potensi_rupiah, dsb.

    Return
    ------
    str
        Teks narasi Nota Dinas yang telah tersusun lengkap.
    """
    bagian = []
    for tpl_key in ("tpl_pembuka", "tpl_isi", "tpl_penutup"):
        template_teks = st.session_state.get(tpl_key, "")
        try:
            bagian.append(template_teks.format(**data))
        except KeyError as e:
            # Jika ada placeholder pada template kustom yang tidak dikenali,
            # tampilkan pesan yang jelas alih-alih membuat aplikasi crash.
            bagian.append(
                f"[GAGAL MEMPROSES TEMPLATE: placeholder {e} tidak ditemukan pada data]"
            )
    return "\n\n".join(bagian)


def siapkan_data_narasi(
    nama_wp, npwp, jenis_wp, kpp, ar, tahun_pajak,
    jenis_indikasi, sumber_data, uraian_temuan, potensi,
    jenis_pajak, tindak_lanjut, batas_hari,
    dasar_hukum=DASAR_HUKUM_DEFAULT,
) -> dict:
    """Merapikan dan menstandardisasi seluruh input mentah dari form/baris data
    batch menjadi kamus placeholder siap pakai untuk fungsi `generate_narasi`.
    """
    npwp_formatted = format_npwp(npwp)
    tahun_str = tahun_pajak if isinstance(tahun_pajak, str) else ", ".join(tahun_pajak)
    sumber_str = sumber_data if isinstance(sumber_data, str) else ", ".join(sumber_data)
    pajak_str = jenis_pajak if isinstance(jenis_pajak, str) else ", ".join(jenis_pajak)
    batas_waktu_tgl = hitung_tanggal_batas(batas_hari)

    return {
        "nomor_draf": buat_nomor_draf(),
        "tanggal": tanggal_indonesia(date.today()),
        "kepada": "Kepala Kantor Wilayah DJP",
        "dari": f"{ar} - Account Representative/Tim Pengawas, {kpp}",
        "hal": f"Hasil Analisis dan Rekomendasi Pengawasan a.n. {nama_wp}",
        "kpp": kpp,
        "ar": ar,
        "nama_wp": nama_wp,
        "npwp": npwp_formatted,
        "jenis_wp": jenis_wp,
        "tahun_pajak": tahun_str,
        "jenis_indikasi": jenis_indikasi,
        "sumber_data": sumber_str,
        "uraian_temuan": uraian_temuan if uraian_temuan else "tidak terdapat catatan tambahan",
        "potensi_rupiah": format_rupiah(potensi),
        "potensi_terbilang": terbilang(potensi),
        "jenis_pajak": pajak_str,
        "tindak_lanjut": tindak_lanjut,
        "batas_waktu": batas_waktu_tgl,
        "batas_hari": batas_hari,
        "dasar_hukum": dasar_hukum,
        "potensi": potensi,
    }


# ====================================================================================
# 7. HEADER APLIKASI
# ====================================================================================

st.markdown("""
<div class="app-header">

<div class="header-logo">
<svg width="48" height="48" viewBox="0 0 24 24">
<path d="M12 2L21 7V17L12 22L3 17V7L12 2Z"
fill="#F4B400"/>
</svg>
</div>

<div>
<h2 style="margin:0;">
Generator Narasi Nota Dinas & LPP
</h2>

<div style="opacity:.85;">
Kanwil Direktorat Jenderal Pajak
</div>
</div>

</div>
""", unsafe_allow_html=True)

# ====================================================================================
# 8. SIDEBAR NAVIGASI
# ====================================================================================

with st.sidebar:
    st.markdown("## Navigasi Sistem")
    modul = st.radio(
        label="Pilih Modul",
    options=[
    "Dashboard",
    "Single-WP Generator",
    "Batch Generator",
    "Template Narasi",
],
        label_visibility="collapsed",
    )
    st.markdown("---")


def modul_dashboard():

    st.subheader("Dashboard Pengawasan")

    col1,col2,col3,col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class='metric-card'>
        <div class='metric-title'>Total Nota Dinas</div>
        <div class='metric-value'>248</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='metric-card'>
        <div class='metric-title'>Total WP</div>
        <div class='metric-value'>173</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='metric-card'>
        <div class='metric-title'>Total Potensi</div>
        <div class='metric-value'>25,4 M</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class='metric-card'>
        <div class='metric-title'>Jumlah KPP</div>
        <div class='metric-value'>6</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    data_temuan = pd.DataFrame({
        "Jenis":[
            "Ekualisasi",
            "Transfer Pricing",
            "ILAP",
            "Nondeductible"
        ],
        "Jumlah":[45,18,33,22]
    })

    fig1 = px.bar(
        data_temuan,
        x="Jenis",
        y="Jumlah",
        title="Jumlah Kasus per Jenis Temuan"
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

    colA,colB = st.columns(2)

    with colA:

        fig2 = px.pie(
            names=[
                "WP Badan",
                "WP OP"
            ],
            values=[
                140,
                33
            ],
            title="Komposisi Wajib Pajak"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    with colB:

        data_kpp = pd.DataFrame({
            "KPP":[
                "KPP 1",
                "KPP 2",
                "KPP 3",
                "KPP 4"
            ],
            "Kasus":[
                35,
                42,
                21,
                18
            ]
        })

        fig3 = px.bar(
            data_kpp,
            x="KPP",
            y="Kasus",
            title="Kasus per KPP"
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )
        
# ====================================================================================
# 9. MODUL 1 - SINGLE-WP GENERATOR
# ====================================================================================

def modul_single_wp():
    """Merender antarmuka dan logika untuk Modul 1: analisis kasus per kasus
    (satu Wajib Pajak) melalui form input interaktif.
    """
st.markdown('<div class="info-badge">MODUL 1</div>', unsafe_allow_html=True)
st.subheader("Single-WP Generator — Analisis Kasus Per Kasus")

with st.form("form_single_wp"):
        # ---------------- Profil WP & Unit Kerja ----------------
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Profil WP & Unit Kerja")
        col1, col2, col3 = st.columns(3)
        with col1:
            nama_wp = st.text_input("Nama Wajib Pajak", value="PT Contoh Makmur Sejahtera")
            npwp_input = st.text_input("NPWP (15/16 Digit)", value="012345678901000")
        with col2:
            jenis_wp = st.selectbox("Jenis WP", JENIS_WP_LIST, index=0)
            kpp = st.selectbox("KPP Terdaftar", DAFTAR_KPP, index=0)
        with col3:
            ar = st.text_input("Nama AR / Tim Pengawas", value="Budi Santoso, S.E.")
            tahun_pajak = st.multiselect(
                "Tahun/Masa Pajak", TAHUN_PAJAK_LIST, default=[TAHUN_PAJAK_LIST[1]]
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # ---------------- Detail Temuan & Indikasi ----------------
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Detail Temuan & Indikasi")
        col4, col5 = st.columns(2)
        with col4:
            jenis_indikasi = st.selectbox("Jenis Indikasi / Modus", JENIS_INDIKASI_LIST, index=0)
            sumber_data = st.multiselect(
                "Sumber Data / Alat Keterangan",
                SUMBER_DATA_LIST,
                default=[SUMBER_DATA_LIST[0], SUMBER_DATA_LIST[1]],
            )
            potensi = st.number_input(
                "Estimasi Nilai Potensi Pajak (Rp)",
                min_value=0.0,
                value=1_250_000_000.0,
                step=1_000_000.0,
                format="%.2f",
            )
        with col5:
            jenis_pajak = st.multiselect(
                "Jenis Pajak Terutang", JENIS_PAJAK_LIST, default=[JENIS_PAJAK_LIST[0], JENIS_PAJAK_LIST[1]]
            )
            uraian_temuan = st.text_area(
                "Uraian Ringkas Temuan Spasial/Data",
                value=(
                    "Hasil sanding data spasial menunjukkan adanya penambahan luas "
                    "bangunan usaha yang belum tercermin pada laporan keuangan dan "
                    "SPT Tahunan WP."
                ),
                height=110,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # ---------------- Rekomendasi Tindak Lanjut ----------------
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 📌 Rekomendasi Tindak Lanjut (SE-05/PJ/2022)")
        col6, col7 = st.columns(2)
        with col6:
            tindak_lanjut = st.selectbox("Pilihan Tindakan", TINDAK_LANJUT_LIST, index=0)
        with col7:
            batas_hari = st.number_input(
                "Batas Waktu Respon (hari kerja)", min_value=1, max_value=90, value=14, step=1
            )
        st.markdown("</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("🚀 Generate Narasi Nota Dinas")

if submitted:
        if not nama_wp or not npwp_input:
            st.error("Nama Wajib Pajak dan NPWP wajib diisi.")
        else:
            data = siapkan_data_narasi(
                nama_wp=nama_wp,
                npwp=npwp_input,
                jenis_wp=jenis_wp,
                kpp=kpp,
                ar=ar,
                tahun_pajak=tahun_pajak if tahun_pajak else [TAHUN_PAJAK_LIST[0]],
                jenis_indikasi=jenis_indikasi,
                sumber_data=sumber_data if sumber_data else ["Data Internal DJP"],
                uraian_temuan=uraian_temuan,
                potensi=potensi,
                jenis_pajak=jenis_pajak if jenis_pajak else [JENIS_PAJAK_LIST[0]],
                tindak_lanjut=tindak_lanjut,
                batas_hari=batas_hari,
            )
            st.session_state["hasil_narasi_single"] = generate_narasi(data)

if st.session_state["hasil_narasi_single"]:
        st.markdown("---")
        st.markdown("### 📄 Hasil Draf Narasi Nota Dinas")
        st.caption("Gunakan ikon salin (copy) pada pojok kanan atas kotak kode di bawah untuk menyalin teks.")
        st.markdown(
    f"""
    <div class="document-preview">
    {st.session_state["hasil_narasi_single"].replace(chr(10), "<br>")}
    </div>
    """,
    unsafe_allow_html=True
)

        colA, colB = st.columns([1, 5])
        with colA:
            st.download_button(
                label="⬇️ Download Draf (.txt)",
                data=st.session_state["hasil_narasi_single"].encode("utf-8"),
                file_name=f"draf_nota_dinas_{nama_wp.replace(' ', '_')}.txt",
                mime="text/plain",
            )


# ====================================================================================
# 10. MODUL 2 - BATCH / MULTI-WP GENERATOR
# ====================================================================================

def _buat_file_csv_contoh() -> bytes:
    """Membuat file CSV contoh/dummy yang dapat diunduh pengguna sebagai
    acuan format kolom yang benar sebelum melakukan upload data batch.
    """
    contoh = pd.DataFrame(
        {
            "Nama WP": ["PT Contoh Makmur Sejahtera", "CV Berkah Abadi", "Andi Wijaya"],
            "NPWP": ["012345678901000", "023456789012000", "034567890123000"],
            "Jenis WP": ["Wajib Pajak Badan", "Wajib Pajak Badan", "Wajib Pajak Orang Pribadi"],
            "KPP": [DAFTAR_KPP[0], DAFTAR_KPP[1], DAFTAR_KPP[2]],
            "AR": ["Budi Santoso, S.E.", "Siti Rahayu, S.E., M.M.", "Dedi Kurniawan, S.E."],
            "Tahun Pajak": ["2024", "2023", "2024"],
            "Jenis Temuan": [
                "Ekualisasi Omzet PPN vs PPh Badan",
                "Biaya Nondeductible",
                "Objek PPh Potput Belum Dipotong/Disetor",
            ],
            "Sumber Data": [
                "Data Internal DJP",
                "Data ILAP (Instansi, Lembaga, Asosiasi, Pihak Lain)",
                "Hasil Konfirmasi Faktur Pajak",
            ],
            "Uraian Temuan": [
                "Terdapat selisih omzet signifikan antara SPT Masa PPN dan SPT Tahunan PPh Badan.",
                "Ditemukan biaya entertainment tanpa daftar nominatif yang dibebankan sebagai pengurang.",
                "Terdapat objek PPh Pasal 23 atas jasa yang belum dilakukan pemotongan.",
            ],
            "Jenis Pajak": ["PPN, PPh Badan", "PPh Badan", "PPh Pasal 23"],
            "Potensi": [1250000000, 350000000, 85000000],
            "Tindak Lanjut": [TINDAK_LANJUT_LIST[0], TINDAK_LANJUT_LIST[1], TINDAK_LANJUT_LIST[0]],
            "Batas Hari": [14, 14, 7],
        }
    )
    buffer = io.StringIO()
    contoh.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def _baca_file_upload(uploaded_file) -> pd.DataFrame:
    """Membaca file upload (CSV atau Excel) menjadi DataFrame pandas.

    Menangani error jika format file tidak didukung atau file rusak.
    """
    nama_file = uploaded_file.name.lower()
    if nama_file.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if nama_file.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    raise ValueError("Format file tidak didukung. Silakan unggah file .csv, .xlsx, atau .xls.")


def _proses_baris_batch(baris: pd.Series) -> str:
    """Memproses satu baris DataFrame batch menjadi narasi Nota Dinas.

    Melakukan validasi ringan dan pemberian nilai default apabila kolom
    opsional kosong, agar proses batch tidak berhenti akibat satu baris
    yang datanya tidak lengkap.
    """
    jenis_pajak_raw = str(baris.get("Jenis Pajak", JENIS_PAJAK_LIST[0]))
    jenis_pajak_list = [p.strip() for p in jenis_pajak_raw.split(",") if p.strip()]

    sumber_data_raw = str(baris.get("Sumber Data", SUMBER_DATA_LIST[0]))
    sumber_data_list = [s.strip() for s in sumber_data_raw.split(",") if s.strip()]

    tahun_pajak_raw = str(baris.get("Tahun Pajak", TAHUN_PAJAK_LIST[0]))
    tahun_pajak_list = [t.strip() for t in tahun_pajak_raw.split(",") if t.strip()]

    data = siapkan_data_narasi(
        nama_wp=str(baris.get("Nama WP", "-")),
        npwp=str(baris.get("NPWP", "-")),
        jenis_wp=str(baris.get("Jenis WP", JENIS_WP_LIST[0])),
        kpp=str(baris.get("KPP", DAFTAR_KPP[0])),
        ar=str(baris.get("AR", "-")),
        tahun_pajak=tahun_pajak_list if tahun_pajak_list else [TAHUN_PAJAK_LIST[0]],
        jenis_indikasi=str(baris.get("Jenis Temuan", JENIS_INDIKASI_LIST[0])),
        sumber_data=sumber_data_list if sumber_data_list else [SUMBER_DATA_LIST[0]],
        uraian_temuan=str(baris.get("Uraian Temuan", "")),
        potensi=baris.get("Potensi", 0),
        jenis_pajak=jenis_pajak_list if jenis_pajak_list else [JENIS_PAJAK_LIST[0]],
        tindak_lanjut=str(baris.get("Tindak Lanjut", TINDAK_LANJUT_LIST[0])),
        batas_hari=int(baris.get("Batas Hari", 14) or 14),
    )
    return generate_narasi(data)


def modul_batch():
    """Merender antarmuka dan logika untuk Modul 2: Batch/Multi-WP Generator,
    yaitu pembuatan narasi Nota Dinas untuk banyak Wajib Pajak sekaligus
    melalui upload file CSV/Excel.
    """
    st.markdown('<div class="info-badge">MODUL 2</div>', unsafe_allow_html=True)
    st.subheader("Batch / Multi-WP Generator — Upload CSV/Excel")

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### 📥 Unggah Data Wajib Pajak")
    st.write(
        "Kolom yang dibutuhkan: **Nama WP, NPWP, Jenis WP, KPP, AR, Tahun Pajak, "
        "Jenis Temuan, Sumber Data, Uraian Temuan, Jenis Pajak, Potensi, "
        "Tindak Lanjut, Batas Hari**. Belum punya file? Unduh contoh format di bawah."
    )
    st.download_button(
        label="⬇️ Unduh Contoh Format CSV",
        data=_buat_file_csv_contoh(),
        file_name="contoh_data_batch_wp.csv",
        mime="text/csv",
    )
    uploaded_file = st.file_uploader("Pilih file CSV/Excel", type=["csv", "xlsx", "xls"])
    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file is not None:
        try:
            df = _baca_file_upload(uploaded_file)
        except Exception as e:
            st.error(f"Gagal membaca file: {e}. Pastikan format kolom sesuai contoh yang disediakan.")
            return

        kolom_wajib = ["Nama WP", "NPWP", "KPP", "Jenis Temuan", "Potensi"]
        kolom_hilang = [k for k in kolom_wajib if k not in df.columns]
        if kolom_hilang:
            st.error(
                "Kolom wajib berikut tidak ditemukan pada file yang diunggah: "
                f"{', '.join(kolom_hilang)}. Silakan sesuaikan file Anda dengan contoh format."
            )
            return

        st.success(f"File berhasil dibaca. Ditemukan {len(df)} baris data Wajib Pajak.")
        st.dataframe(df, use_container_width=True)

        if st.button("🚀 Proses & Generate Narasi Batch"):
            hasil_narasi = []
            progress = st.progress(0, text="Memproses data...")
            total = len(df)
            for i, (_, baris) in enumerate(df.iterrows()):
                try:
                    narasi = _proses_baris_batch(baris)
                except Exception as e:
                    narasi = f"[GAGAL MEMPROSES BARIS INI: {e}]"
                hasil_narasi.append(narasi)
                progress.progress((i + 1) / total, text=f"Memproses data... ({i + 1}/{total})")

            df_hasil = df.copy()
            df_hasil["Narasi Nota Dinas"] = hasil_narasi
            st.session_state["hasil_batch_df"] = df_hasil
            progress.empty()
            st.success("Seluruh narasi berhasil dibuat.")

    if st.session_state["hasil_batch_df"] is not None:
        df_hasil = st.session_state["hasil_batch_df"]
        st.markdown("---")
        st.markdown("### 📄 Hasil Kompilasi Narasi")

        with st.expander("Lihat tabel hasil lengkap"):
            st.dataframe(df_hasil, use_container_width=True)

        pilihan_preview = st.selectbox(
            "Pilih WP untuk pratinjau narasi",
            options=list(range(len(df_hasil))),
            format_func=lambda i: df_hasil.iloc[i].get("Nama WP", f"Baris {i+1}"),
        )
        st.markdown(
    f"""
    <div class="document-preview">
    {df_hasil.iloc[pilihan_preview]["Narasi Nota Dinas"].replace(chr(10), "<br>")}
    </div>
    """,
    unsafe_allow_html=True
)

        col1, col2 = st.columns(2)
        with col1:
            csv_bytes = df_hasil.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Hasil (.csv)",
                data=csv_bytes,
                file_name="hasil_narasi_batch.csv",
                mime="text/csv",
            )
        with col2:
            gabungan_txt = "\n\n" + ("=" * 90) + "\n\n"
            gabungan_txt = gabungan_txt.join(df_hasil["Narasi Nota Dinas"].tolist())
            st.download_button(
                label="⬇️ Download Hasil (.txt)",
                data=gabungan_txt.encode("utf-8"),
                file_name="hasil_narasi_batch.txt",
                mime="text/plain",
            )


# ====================================================================================
# 11. MODUL 3 - TEMPLATE & CUSTOMIZER NARASI
# ====================================================================================

def modul_template():
    """Merender antarmuka dan logika untuk Modul 3: Template & Customizer,
    yaitu penyesuaian format pembuka, isi, dan penutup narasi Nota Dinas
    secara dinamis menggunakan placeholder.
    """
    st.markdown('<div class="info-badge">MODUL 3</div>', unsafe_allow_html=True)
    st.subheader("Template & Customizer Narasi")

    st.info(
        "Placeholder yang tersedia: {nama_wp}, {npwp}, {jenis_wp}, {kpp}, {ar}, "
        "{tahun_pajak}, {jenis_indikasi}, {sumber_data}, {uraian_temuan}, "
        "{potensi_rupiah}, {potensi_terbilang}, {jenis_pajak}, {tindak_lanjut}, "
        "{batas_waktu}, {batas_hari}, {dasar_hukum}, {nomor_draf}, {tanggal}, "
        "{kepada}, {dari}, {hal}",
        icon="ℹ️",
    )

    with st.form("form_template"):
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### ✏️ Bagian Pembuka (Header Nota Dinas)")
        tpl_pembuka = st.text_area(
            "Template Pembuka", value=st.session_state["tpl_pembuka"], height=200
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### ✏️ Bagian Isi (Uraian & Temuan)")
        tpl_isi = st.text_area(
            "Template Isi", value=st.session_state["tpl_isi"], height=260
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### ✏️ Bagian Penutup (Rekomendasi & Penutup)")
        tpl_penutup = st.text_area(
            "Template Penutup", value=st.session_state["tpl_penutup"], height=200
        )
        st.markdown("</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            simpan = st.form_submit_button("💾 Simpan Template")
        with col2:
            reset = st.form_submit_button("♻️ Kembalikan ke Default")

    if simpan:
        st.session_state["tpl_pembuka"] = tpl_pembuka
        st.session_state["tpl_isi"] = tpl_isi
        st.session_state["tpl_penutup"] = tpl_penutup
        st.success("Template narasi berhasil disimpan dan akan digunakan pada Modul 1 & Modul 2.")

    if reset:
        st.session_state["tpl_pembuka"] = DEFAULT_TEMPLATE_PEMBUKA
        st.session_state["tpl_isi"] = DEFAULT_TEMPLATE_ISI
        st.session_state["tpl_penutup"] = DEFAULT_TEMPLATE_PENUTUP
        st.success("Template berhasil dikembalikan ke pengaturan default.")
        st.rerun()

    st.markdown("---")
    st.markdown("### 👀 Pratinjau Template dengan Data Contoh")
    if st.button("Tampilkan Pratinjau"):
        data_contoh = siapkan_data_narasi(
            nama_wp="PT Contoh Makmur Sejahtera",
            npwp="012345678901000",
            jenis_wp=JENIS_WP_LIST[0],
            kpp=DAFTAR_KPP[0],
            ar="Budi Santoso, S.E.",
            tahun_pajak=["2024"],
            jenis_indikasi=JENIS_INDIKASI_LIST[0],
            sumber_data=[SUMBER_DATA_LIST[0], SUMBER_DATA_LIST[1]],
            uraian_temuan="Contoh uraian temuan hasil analisis data pengawasan.",
            potensi=1_250_000_000,
            jenis_pajak=[JENIS_PAJAK_LIST[0], JENIS_PAJAK_LIST[1]],
            tindak_lanjut=TINDAK_LANJUT_LIST[0],
            batas_hari=14,
        )
        st.code(generate_narasi(data_contoh), language="text")


# ====================================================================================
# 12. ROUTING ANTAR MODUL
# ====================================================================================

if "Dashboard" in modul:
    modul_dashboard()

elif "Single" in modul:
    modul_single_wp()

elif "Batch" in modul:
    modul_batch()

else:
    modul_template()

# ====================================================================================
# 13. FOOTER
# ====================================================================================

st.markdown(
    """
    <div class="app-footer">
        Generator Narasi Nota Dinas &amp; LPP — Kanwil DJP · Dibuat untuk mendukung efisiensi
        administrasi pengawasan perpajakan · Seluruh draf wajib direviu oleh pejabat berwenang
        sebelum diterbitkan sebagai dokumen resmi.
    </div>
    """,
    unsafe_allow_html=True,
)