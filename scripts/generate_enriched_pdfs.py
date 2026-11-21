"""Script to generate enriched government scheme PDFs for SchemeSaathi.

Includes:
- Detailed scheme objectives and benefits
- Eligibility and exclusion criteria
- Step-by-step 'How to Apply' (online and offline)
- 'Nearest Application Centers' (CSC, e-Sevai, Ration shops, VAO offices)
- 'Needed Documents Checklist' (Aadhaar, Land Patta, Bank Passbook, Ration Card)
- 'Portal Application Clarification' (SchemeSaathi guides citizens; official submission is via official portals/centers)
"""

from pathlib import Path
import fitz

DATA_RAW_DIR = Path("data/raw")
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)


def build_pm_kisan_pdf():
    """Build enriched PM-KISAN guideline PDF in English."""
    doc = fitz.open()
    rect = fitz.Rect(50, 50, 545, 790)

    # --- Page 1: Overview, Objectives & Eligibility ---
    p1 = doc.new_page(width=595, height=842)
    text_p1 = (
        "GOVERNMENT OF INDIA - MINISTRY OF AGRICULTURE AND FARMERS WELFARE\n"
        "PRADHAN MANTRI KISAN SAMMAN NIDHI (PM-KISAN) OPERATIONAL GUIDELINES\n\n"
        "1. Introduction and Objectives:\n"
        "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) is a Central Sector Scheme with 100% funding from the Government of India. "
        "Under the scheme, the Central Government provides financial assistance and income support of Rs. 6,000 per year to eligible "
        "farmer families across the country. The financial benefit is disbursed in three equal four-monthly installments of Rs. 2,000 each "
        "directly into the bank accounts of the beneficiaries through Direct Benefit Transfer (DBT).\n\n"
        "2. Definition of Eligible Farmer Families:\n"
        "A landholder farmer family is defined as a family comprising husband, wife, and minor children who own cultivable land as per the "
        "land records of the respective State or Union Territory.\n\n"
        "3. Exclusion Categories (Who Cannot Apply):\n"
        "The following categories of beneficiaries of higher economic status are strictly excluded from receiving PM-KISAN benefits:\n"
        "(a) All Institutional Landholders.\n"
        "(b) Farmer families holding constitutional posts, former and present Ministers, Members of Parliament (MPs), and Members of Legislative Assemblies (MLAs).\n"
        "(c) All serving or retired officers and employees of Central/State Government ministries and public sector undertakings.\n"
        "(d) All persons who paid Income Tax in the last assessment year.\n"
        "(e) Professionals like Doctors, Engineers, Lawyers, Chartered Accountants, and Architects registered with professional bodies.\n"
        "(f) All superannuated/retired pensioners whose monthly pension is Rs. 10,000 or more."
    )
    p1.insert_textbox(rect, text_p1, fontsize=10, fontname="helv")

    # --- Page 2: Verification, Grievances & Monitoring ---
    p2 = doc.new_page(width=595, height=842)
    text_p2 = (
        "GOVERNMENT OF INDIA - MINISTRY OF AGRICULTURE AND FARMERS WELFARE\n"
        "PRADHAN MANTRI KISAN SAMMAN NIDHI (PM-KISAN) OPERATIONAL GUIDELINES\n\n"
        "4. Method of Identification and Verification:\n"
        "The identification and verification of eligible farmer families is the sole responsibility of the respective State and Union Territory Governments. "
        "Verification is conducted using State land record databases, physical spot inspections, and mandatory Aadhaar-based electronic Know Your Customer (e-KYC).\n\n"
        "5. Grievance Redressal and Helpline:\n"
        "Beneficiaries can register grievances, track payment status, or resolve payment failures through the PM-KISAN official portal (pmkisan.gov.in) "
        "or by contacting the toll-free national helpline number 155261 or 1800115526. A District Level Grievance Redressal Committee headed by the "
        "District Collector / District Magistrate reviews citizen complaints on a regular basis."
    )
    p2.insert_textbox(rect, text_p2, fontsize=10, fontname="helv")

    # --- Page 3: How to Apply, Nearest Centers, Needed Documents & Portal Clarification ---
    p3 = doc.new_page(width=595, height=842)
    text_p3 = (
        "GOVERNMENT OF INDIA - MINISTRY OF AGRICULTURE AND FARMERS WELFARE\n"
        "PRADHAN MANTRI KISAN SAMMAN NIDHI (PM-KISAN) OPERATIONAL GUIDELINES\n\n"
        "6. How to Apply for PM-KISAN (Application Process):\n"
        "(a) Online Mode (Self-Registration): Farmers can visit the official PM-KISAN portal (https://pmkisan.gov.in) and navigate to the 'Farmers Corner'. "
        "Click on 'New Farmer Registration', select Rural or Urban Farmer Registration, enter your Aadhaar number and mobile number, verify with Aadhaar OTP, "
        "and fill in personal, bank, and landholding details.\n"
        "(b) Mobile App: Farmers can also register through the official PM-KISAN Mobile App which supports biometric face-authentication e-KYC.\n"
        "(c) Assisted Offline Mode: Farmers who cannot register online can visit an authorized application center in person.\n\n"
        "7. Nearest Centers to Apply:\n"
        "Farmers can apply through the following nearby physical service centers:\n"
        "• Common Service Centres (CSC / Digital Seva Kendras) located in village panchayats and towns.\n"
        "• Village Administrative Officer (VAO) office and local Revenue Department offices.\n"
        "• District Agriculture Department Offices, Block Development Offices (BDO), and Krishi Vigyan Kendras (KVK).\n\n"
        "8. Needed Documents Checklist:\n"
        "To apply for PM-KISAN, the following official documents are mandatory:\n"
        "1. Aadhaar Card (mandatory for identity verification and e-KYC).\n"
        "2. Land Ownership Documents (Updated Patta, Chitta, Khatauni, or Record of Rights proving cultivable land ownership).\n"
        "3. Bank Account Passbook (active bank account with IFSC code; bank account MUST be Aadhaar-seeded and NPCI-mapped for DBT payments).\n"
        "4. Active Mobile Number linked to Aadhaar (for OTP verification and payment status SMS).\n"
        "5. Identity & Residence Proof.\n\n"
        "9. Can Citizens Apply Directly via the SchemeSaathi Portal?:\n"
        "No. SchemeSaathi is an informational and advisory AI guidance assistant. It is NOT possible to apply directly or submit official applications "
        "through this SchemeSaathi chat portal. SchemeSaathi helps you check eligibility criteria, provides the complete required documents checklist, "
        "and guides you to the nearest Common Service Centre (CSC) or the official government application portal (pmkisan.gov.in)."
    )
    p3.insert_textbox(rect, text_p3, fontsize=9.2, fontname="helv")

    pdf_out = DATA_RAW_DIR / "pm_kisan.pdf"
    doc.save(str(pdf_out))
    doc.close()
    print(f"Generated {pdf_out} (3 pages)")


def build_kmut_pdf():
    """Build enriched Kalaignar Magalir Urimai guideline PDF in Tamil with Nirmala font."""
    font_path = Path("C:/Windows/Fonts/Nirmala.ttc")
    if not font_path.exists():
        raise FileNotFoundError(f"Font not found: {font_path}")

    font_bytes = font_path.read_bytes()
    doc = fitz.open()
    rect = fitz.Rect(50, 50, 545, 790)

    # --- Page 1: Overview, Objectives & Eligibility ---
    p1 = doc.new_page(width=595, height=842)
    p1.insert_font(fontname="Nirmala", fontbuffer=font_bytes)
    text_p1 = (
        "தமிழ்நாடு அரசு ‐ சிறப்புத் திட்ட செயலாக்கத் துறை\n"
        "கலைஞர் மகளிர் உரிமைத் திட்டம் வழிகாட்டு நெறிமுறைகள்\n\n"
        "1. திட்டத்தின் நோக்கம் மற்றும் உதவித்தொகை:\n"
        "தமிழ்நாட்டில் குடும்பத் தலைவிகளாக விளங்கும் பெண்களின் வாழ்வாதாரத்தை மேம்படுத்தவும் அவர்களின் உழைப்பை அங்கீகரிக்கவும் "
        "மாதந்தோறும் ரூ. 1,000 உரிமைத் தொகை வழங்கும் வரலாற்று சிறப்புமிக்க திட்டமாக கலைஞர் மகளிர் உரிமைத் திட்டம் செயல்படுத்தப்படுகிறது. "
        "இத்தொகை பயனாளிகளின் வங்கிக் கணக்கில் நேரடியாக வரவு வைக்கப்படுகிறது.\n\n"
        "2. தகுதி வரம்புகள்:\n"
        "(அ) விண்ணப்பதாரர் தமிழ்நாட்டில் குடும்ப அட்டை (ரேஷன் கார்டு) வைத்துள்ள நிரந்தர வசிப்பவராக இருத்தல் வேண்டும்.\n"
        "(ஆ) குடும்பத்தின் ஆண்டு வருமானம் ரூ. 2.50 இலட்சத்திற்கு குறைவாக இருக்க வேண்டும்.\n"
        "(இ) குடும்பத்தினருக்கு 5 ஏக்கருக்கு குறைவாக நன்செய் நிலம் அல்லது 10 ஏக்கருக்கு குறைவாக புன்செய் நிலம் இருத்தல் வேண்டும்.\n"
        "(ஈ) குடும்பத்தின் ஆண்டு மின்சார பயன்பாடு 3,600 யூனிட்டுகளுக்கு குறைவாக இருக்க வேண்டும்.\n"
        "(உ) 21 வயது பூர்த்தியடைந்த குடும்பத் தலைவிகள் இத்திட்டத்திற்கு விண்ணப்பிக்க தகுதியுடையவர்கள்.\n\n"
        "3. தகுதியின்மை வரம்புகள்:\n"
        "குடும்பத்தில் எவரேனும் வருமான வரி செலுத்துபவர்கள், அரசு ஊழியர்கள், பொதுத்துறை நிறுவன ஊழியர்கள், மற்றும் "
        "நான்கு சக்கர வாகனம் (கார், ஜீப்) சொந்தமாக வைத்துள்ள குடும்பங்கள் இத்திட்டத்தின் கீழ் பயன்பெற இயலாது."
    )
    p1.insert_textbox(rect, text_p1, fontsize=10, fontname="Nirmala")

    # --- Page 2: How to Apply, Nearest Centers, Needed Documents & Portal Clarification ---
    p2 = doc.new_page(width=595, height=842)
    p2.insert_font(fontname="Nirmala", fontbuffer=font_bytes)
    text_p2 = (
        "தமிழ்நாடு அரசு ‐ சிறப்புத் திட்ட செயலாக்கத் துறை\n"
        "கலைஞர் மகளிர் உரிமைத் திட்டம் வழிகாட்டு நெறிமுறைகள்\n\n"
        "4. விண்ணப்பிக்கும் முறை (How to Apply):\n"
        "கலைஞர் மகளிர் உரிமைத் திட்டத்திற்கு விண்ணப்பங்கள் சிறப்பு முகாம்கள் மூலமாக பெறப்படுகின்றன:\n"
        "(அ) விண்ணப்ப படிவம் மற்றும் டோக்கன்: நியாயவிலைக் கடை (ரேஷன் கடை) பணியாளர்கள் தகுதியுடைய குடும்பங்களின் வீடு தேடிச் சென்று "
        "விண்ணப்பப் படிவம் மற்றும் முகாம் நாள்/நேரம் குறிப்பிடப்பட்ட டோக்கன்களை வழங்குவார்கள்.\n"
        "(ஆ) முகாமில் பதிவு செய்தல்: டோக்கனில் குறிப்பிடப்பட்டுள்ள நாளில், உங்கள் நியாயவிலைக் கடைக்கு அருகிலுள்ள சிறப்பு முகாமிற்கு "
        "பூர்த்தி செய்த விண்ணப்பத்துடன் நேரில் செல்ல வேண்டும்.\n"
        "(இ) கைரேகை மற்றும் சரிபார்ப்பு: முகாமில் உள்ள தன்னார்வலர்கள் மற்றும் அரசு அலுவலர்கள் விண்ணப்பத்தை சரிபார்த்து பயோமெட்ரிக் "
        "(கைரேகை) பதிவு செய்து ஒப்புகைச் சீட்டு வழங்குவார்கள்.\n\n"
        "5. விண்ணப்பிக்க அருகிலுள்ள சேவை மையங்கள் (Nearest Centers to Apply):\n"
        "விண்ணப்பதாரர்கள் பின்வரும் அருகிலுள்ள மையங்கள் மூலம் வழிகாட்டுதலையும் உதவியையும் பெறலாம்:\n"
        "• உங்கள் பகுதி நியாயவிலைக் கடை / ரேஷன் கடை சிறப்பு முகாம்கள் (Fair Price Shop Camps).\n"
        "• தமிழ்நாடு அரசு இ-சேவை மையங்கள் (TN e-Sevai Centers / TNeGA) மற்றும் பொதுச் சேவை மையங்கள் (CSC).\n"
        "• வட்டாட்சியர் அலுவலகம் (Taluk Office / Tahsildar Office) மற்றும் வருவாய் துறை உதவி மையங்கள்.\n"
        "• கிராம நிர்வாக அலுவலர் (VAO) அலுவலகம்.\n\n"
        "6. விண்ணப்பிக்க தேவையான ஆவணங்கள் (Needed Documents Checklist):\n"
        "விண்ணப்பிக்க பின்வரும் அசல் ஆவணங்கள் சரிபார்ப்பிற்கு அவசியமாகும்:\n"
        "1. குடும்ப அட்டை (Ration Smart Card).\n"
        "2. விண்ணப்பதாரரின் ஆதார் அட்டை (Aadhaar Card).\n"
        "3. ஆதார் இணைக்கப்பட்ட வங்கிக் கணக்கு புத்தகம் (Bank Passbook with Aadhaar and NPCI linkage).\n"
        "4. மின்சார கட்டண அட்டை அல்லது மின் இணைப்பு நுகர்வோர் எண் ரசீது (Electricity Bill).\n"
        "5. நில உடமை ஆவணங்கள் (பட்டா / சிட்டா - நிலம் வைத்திருப்பின்).\n"
        "6. ஆதாருடன் இணைக்கப்பட்ட கைபேசி எண் (Mobile Number linked to Aadhaar).\n\n"
        "7. இந்த இணையதளத்தில் (SchemeSaathi) நேரடியாக விண்ணப்பிக்க முடியுமா?:\n"
        "இல்லை. SchemeSaathi என்பது வழிகாட்டுதல் மற்றும் தகவல் வழங்கும் AI உதவி தளம் மட்டுமே. இத்தளத்தின் மூலம் நேரடியாக அதிகாரப்பூர்வ "
        "விண்ணப்பங்களை சமர்ப்பிக்க முடியாது. தகுதியுடைய பெண்கள் தமிழ்நாடு அரசு நடத்தும் சிறப்பு முகாம்கள் அல்லது இ-சேவை மையங்கள் மூலமாகவே "
        "விண்ணப்பிக்க வேண்டும். இத்தளம் தேவையான ஆவணங்கள் மற்றும் மையங்களை கண்டறிய வழிகாட்டுகிறது."
    )
    p2.insert_textbox(rect, text_p2, fontsize=9.2, fontname="Nirmala")

    pdf_out = DATA_RAW_DIR / "kalaignar_magalir_urimai.pdf"
    doc.save(str(pdf_out))
    doc.close()
    print(f"Generated {pdf_out} (2 pages)")


if __name__ == "__main__":
    build_pm_kisan_pdf()
    build_kmut_pdf()
