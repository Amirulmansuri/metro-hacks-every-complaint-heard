import streamlit as st, sqlite3, re, socket, requests, pandas as pd

DB = "complaints.db"
MODEL = "gemma3:4b"  
LANGN = {"en": "English", "hi": "Hindi", "gu": "Gujarati", "gujlish": "English"}

KW = {
    "Safety": ["fire", "smoke", "aag", "dhuaan", "fight", "jhagda", "harass", "eve teas", "chhedchhad",
               "accident", "injur", "emergency", "bachao", "unsafe", "theft", "chori", "stuck", "fas gaya",
               "trapped", "locked", "door lock", "door is lock",
               "આગ", "ધુમાડો", "સુરક્ષા", "ઝઘડો", "ચોરી", "छेड़", "आग", "धुआं", "सुरक्षा", "झगड़ा", "चोरी"],
    "Cleanliness": ["dirty", "gandu", "gandi", "kachra", "garbage", "smell", "badbu", "washroom", "toilet",
                    "dustbin", "spit", "ગંદ", "કચરો", "દુર્ગંધ", "શૌચાલય", "गंदा", "गंदगी", "कचरा", "बदबू", "शौचालय"],
    "Fare": ["fare", "refund", "paise", "ticket", "card", "recharge", "balance", "deducted", "double charge",
             "bhada", "ભાડું", "ટિકિટ", "કાર્ડ", "રિફંડ", "પૈસા", "किराया", "टिकट", "कार्ड", "रिफंड", "पैसे"],
    "Lifts": ["lift", "escalator", "elevator", "stairs", "wheelchair", "લિફ્ટ", "એસ્કેલેટર",
              "लिफ्ट", "एस्केलेटर", "सीढ़ी"],
    "Staff Behaviour": ["rude", "staff", "guard", "behaviour", "behavior", "misbehave", "badtameez", "gussa",
                        "કર્મચારી", "વર્તન", "ગાર્ડ", "બદતમીજ", "स्टाफ", "बदतमीज", "व्यवहार", "गार्ड"],
}
URGENT = ["urgent", "emergency", "immediately", "turant", "abhi", "jaldi", "help", "child", "bachcha",
          "senior", "pregnant", "stuck", "tarat", "તાત્કાલિક", "તરત", "જલ્દી", "બચાવો", "तुरंत", "फौरन",
          "जल्दी", "बचाओ", "बच्चा", "बुजुर्ग"]
BASE = {"Safety": 60, "Lifts": 35, "Staff Behaviour": 30, "Fare": 25, "Cleanliness": 20, "General": 10}

REPLY = {
    "Safety": {
        "en": "Thank you for reporting. Our safety team has been alerted and staff are being sent immediately.",
        "hi": "सूचना देने के लिए धन्यवाद। हमारी सुरक्षा टीम को अलर्ट कर दिया गया है और स्टाफ तुरंत भेजा जा रहा है।",
        "gu": "જાણ કરવા બદલ આભાર. અમારી સુરક્ષા ટીમને જાણ કરી દેવામાં આવી છે અને સ્ટાફને તરત મોકલવામાં આવી રહ્યો છે."},
    "Cleanliness": {
        "en": "Sorry for the inconvenience. The housekeeping team has been informed and will clean the area shortly.",
        "hi": "असुविधा के लिए खेद है। हाउसकीपिंग टीम को सूचित कर दिया गया है, जल्द सफाई होगी।",
        "gu": "અસુવિધા બદલ ક્ષમા. હાઉસકીપિંગ ટીમને જાણ કરી છે, જલ્દી સફાઈ કરવામાં આવશે."},
    "Fare": {
        "en": "Your fare issue is logged. Please keep your ticket/card details; our fare team will contact you within 48 hours.",
        "hi": "आपकी किराया संबंधी शिकायत दर्ज कर ली गई है। कृपया टिकट/कार्ड विवरण रखें, टीम 48 घंटे में संपर्क करेगी।",
        "gu": "તમારી ભાડા અંગેની ફરિયાદ નોંધાઈ ગઈ છે. કૃપા કરીને ટિકિટ/કાર્ડની વિગતો રાખો, ટીમ 48 કલાકમાં સંપર્ક કરશે."},
    "Lifts": {
        "en": "Thank you. The maintenance team has been alerted about the lift/escalator; staff will assist passengers meanwhile.",
        "hi": "धन्यवाद। लिफ्ट/एस्केलेटर के लिए मेंटेनेंस टीम को सूचित कर दिया गया है, तब तक स्टाफ यात्रियों की मदद करेगा।",
        "gu": "આભાર. લિફ્ટ/એસ્કેલેટર માટે મેન્ટેનન્સ ટીમને જાણ કરી છે, ત્યાં સુધી સ્ટાફ મુસાફરોને મદદ કરશે."},
    "Staff Behaviour": {
        "en": "We are sorry for your experience. Your complaint has been forwarded to the station manager for action.",
        "hi": "आपके अनुभव के लिए खेद है। शिकायत कार्रवाई हेतु स्टेशन मैनेजर को भेज दी गई है।",
        "gu": "તમારા અનુભવ બદલ ક્ષમા. ફરિયાદ કાર્યવાહી માટે સ્ટેશન મેનેજરને મોકલી દેવામાં આવી છે."},
    "General": {
        "en": "Thank you for your feedback. It has been logged and will be reviewed.",
        "hi": "आपके सुझाव के लिए धन्यवाद। इसे दर्ज कर लिया गया है।",
        "gu": "તમારા પ્રતિભાવ બદલ આભાર. તે નોંધી લેવામાં આવ્યો છે."},
}

SAMPLES = [
    "Lift number 2 is not working since morning, my father is on wheelchair, please help urgent!",
    "ટ્રેનમાં ધુમાડો દેખાય છે, તાત્કાલિક મદદ કરો!",
    "प्लेटफॉर्म पर बहुत गंदगी है और शौचालय से बदबू आ रही है",
    "Card recharge karyu 200 nu pan balance ma paisa nathi aavya, refund joiye che",
    "ગેટ પર ગાર્ડ બહુ બદતમીજીથી વાત કરે છે",
    "टिकट के पैसे दो बार कट गए, रिफंड चाहिए",
    "Escalator band che, senior citizens ne bahu problem che",
    "Platform par kachra pado che, dustbin bhari gayu che",
    "Staff was very rude to a woman passenger at gate 2, please take action",
    "Some men are harassing girls near the exit, please send guard immediately!",
    "સ્ટેશન પર સારી સુવિધા છે, આભાર",
    "Train time table app ma update karo",
]

GUJLISH = r"(?<![\w'])(che|chhe|nathi|nahi|hai|hain|kaam|karyu|joiye|aavya|bahu|abhi|ma|ne|par|pan)(?![\w'])"


def lang(t):
    if re.search(r"[\u0A80-\u0AFF]", t): return "gu"
    if re.search(r"[\u0900-\u097F]", t): return "hi"
    if re.search(GUJLISH, t.lower()): return "gujlish"
    return "en"


def llm_reply(text, dept, l):
    try:
        p = (f"You are a Gujarat Metro support officer. Write a polite 2-sentence reply in {LANGN[l]} "
             f"to this {dept} complaint. Reply text only.\nComplaint: {text}")
        r = requests.post("http://localhost:11434/api/generate",
                          json={"model": MODEL, "prompt": p, "stream": False}, timeout=90)
        return r.json()["response"].strip()
    except Exception:
        return None


def llm_dept(text):
    """Gemma fallback: only used when no keyword matches."""
    try:
        p = ("Classify this metro passenger complaint into exactly one of: "
             "Safety, Cleanliness, Fare, Lifts, Staff Behaviour, General. "
             f"Reply with the category name only.\nComplaint: {text}")
        r = requests.post("http://localhost:11434/api/generate",
                          json={"model": MODEL, "prompt": p, "stream": False}, timeout=30)
        a = r.json()["response"].strip().lower()
        return next((d for d in BASE if d.lower() in a), None)
    except Exception:
        return None


def triage(t, use_llm=False):
    tl = t.lower()
    scores = {d: sum(k in tl for k in ks) for d, ks in KW.items()}
    d = max(scores, key=scores.get)
    if scores[d] == 0:
        d = (llm_dept(t) if use_llm else None) or "General"
    u = min(100, BASE[d] + 15 * sum(k in tl for k in URGENT) + 5 * t.count("!"))
    l = lang(t)
    return d, u, l, REPLY[d]["en" if l == "gujlish" else l]


def online():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2).close()
        return True
    except OSError:
        return False


def db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS c(id INTEGER PRIMARY KEY, text TEXT, lang TEXT, dept TEXT, "
              "urgency INT, reply TEXT, synced INT DEFAULT 0)")
    return c


def add(t, use_llm=False):
    with db() as c:
        if c.execute("SELECT 1 FROM c WHERE text=?", (t,)).fetchone():
            return  # duplicate skip
    d, u, l, r = triage(t, use_llm)
    with db() as c:
        c.execute("INSERT INTO c(text,lang,dept,urgency,reply) VALUES(?,?,?,?,?)", (t, l, d, u, r))


# ---------------- UI ----------------
st.set_page_config(page_title="Every Complaint Heard", layout="wide")
st.title("🚇 Every Complaint Heard: Offline Complaint Triage")

force_off = st.sidebar.toggle("Simulate offline (demo)")
net = online() and not force_off
st.sidebar.metric("Network", "Online" if net else "OFFLINE")
st.sidebar.caption("Triage runs fully on-device. Data syncs when network returns.")

c1, c2 = st.columns([3, 1])
with c1:
    txt = st.text_area("New complaint (ગુજરાતી / हिन्दी / English / Gujlish = Gujarati in English letters)")
    if st.button("Triage complaint") and txt.strip():
        with st.spinner("Triaging..."):
            add(txt.strip(), use_llm=True)
        st.rerun()
with c2:
    if st.button("Load 12 sample complaints"):
        for s in SAMPLES: add(s)
        st.rerun()
    if st.button("Clear all"):
        with db() as c: c.execute("DELETE FROM c")
        st.rerun()

df = pd.read_sql("SELECT * FROM c ORDER BY urgency DESC", db())
if df.empty:
    st.info("Koi complaint nahi. Sample load karo.")
    st.stop()

pending = int((df.synced == 0).sum())
m1, m2, m3 = st.columns(3)
m1.metric("Total", len(df)); m2.metric("Critical (urgency ≥ 70)", int((df.urgency >= 70).sum()))
m3.metric("Pending sync", pending)

if st.button(f"Sync {pending} pending to control room"):
    if net:
        with db() as c: c.execute("UPDATE c SET synced=1")  # real life: POST to server here
        st.success("Synced!"); st.rerun()
    else:
        st.warning("No network. Saved locally, will sync at next station.")

dept = st.selectbox("Department queue", ["All"] + sorted(df.dept.unique()))
view = df if dept == "All" else df[df.dept == dept]
st.dataframe(view[["id", "urgency", "dept", "lang", "text", "synced"]], use_container_width=True, hide_index=True)

st.subheader("Draft reply")
cid = st.selectbox("Complaint ID", view.id.tolist())
row = df[df.id == cid].iloc[0]
st.write(f"**{row.dept}** | urgency **{row.urgency}** | language **{row.lang}**")
st.text_area("Reply (template)", row.reply, height=100)
if st.button("✨ Improve reply with on-device Gemma"):
    with st.spinner("Gemma soch raha hai..."):
        r = llm_reply(row.text, row.dept, row.lang)
    st.text_area("Gemma reply", r or "Gemma not available, template reply use karo.", height=120)
