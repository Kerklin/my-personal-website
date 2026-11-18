"""Architectural portfolio website: Streamlit + Supabase contact form.

All content is read from profile_data.yaml. Edit that file, not this one.
Run locally:  streamlit run app.py
"""

from __future__ import annotations

import html
import os
import re
import time
from pathlib import Path

import streamlit as st
import yaml
from PIL import Image

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "profile_data.yaml"
ASSETS = ROOT / "assets"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
HEADSHOT_WORDS = ("headshot", "portrait", "profile", "photo")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
SUBMIT_COOLDOWN_S = 60

st.set_page_config(page_title="Damir Hadžić | Portfolio", page_icon="▪", layout="wide")


# ---------------------------------------------------------------- data
@st.cache_data
def load_profile() -> dict:
    with open(DATA_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def esc(value) -> str:
    return html.escape(str(value or ""))


def scan_assets() -> tuple[Path | None, list[Path]]:
    """Return (headshot, gallery_images) from assets/."""
    if not ASSETS.is_dir():
        return None, []
    images = sorted(p for p in ASSETS.iterdir() if p.suffix.lower() in IMAGE_EXT)
    headshot = next((p for p in images if any(w in p.stem.lower() for w in HEADSHOT_WORDS)), None)
    return headshot, [p for p in images if p != headshot]


def caption_from(path: Path) -> str:
    return re.sub(r"[_\-]+", " ", path.stem).strip().title()


def get_secret(name: str) -> str:
    """st.secrets first, then environment variables / .env."""
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # no secrets.toml present
        pass
    if not os.getenv(name) and (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return os.getenv(name, "")


# ---------------------------------------------------------------- style
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Cormorant+Garamond:wght@400;500&display=swap');
:root { --bg:#F8F7F4; --ink:#1C1C1C; --line:#E0DDD7; --slate:#5E6670; --bronze:#7A6A53; }
html, body, [class*="css"], .stApp { background:var(--bg); color:var(--ink);
  font-family:'Inter',sans-serif; font-weight:300; }
.block-container { max-width:1180px; padding-top:4.5rem; padding-bottom:4rem; }
header[data-testid="stHeader"] { background:transparent; }
#MainMenu, footer { visibility:hidden; }
a { color:var(--ink); text-decoration:none; border-bottom:1px solid var(--line); }
a:hover { color:var(--bronze); border-color:var(--bronze); }

.topnav { position:fixed; top:0; left:0; right:0; z-index:999; background:rgba(248,247,244,.94);
  backdrop-filter:blur(6px); border-bottom:1px solid var(--line); }
.topnav-inner { max-width:1180px; margin:0 auto; padding:.9rem 1.5rem; display:flex;
  justify-content:space-between; align-items:center; }
.topnav .mark { font-size:.78rem; letter-spacing:.32em; text-transform:uppercase; font-weight:500; }
.topnav nav a { border:none; margin-left:1.8rem; font-size:.7rem; letter-spacing:.22em;
  text-transform:uppercase; color:var(--slate); }
.topnav nav a:hover { color:var(--ink); }

.hero-name { font-family:'Cormorant Garamond',serif; font-size:clamp(2.8rem,6vw,5rem);
  font-weight:400; line-height:1; letter-spacing:-.01em; margin:2.5rem 0 1rem; }
.hero-meta { font-size:.75rem; letter-spacing:.28em; text-transform:uppercase; color:var(--slate); }
.hero-rule { border-top:1px solid var(--ink); margin:2rem 0 3rem; }

.sec { font-size:.72rem; letter-spacing:.34em; text-transform:uppercase; font-weight:500;
  padding:3.2rem 0 .9rem; border-bottom:1px solid var(--line); margin-bottom:2rem; scroll-margin-top:5rem; }
.sec span { color:var(--bronze); margin-right:.8rem; }
.label { font-size:.66rem; letter-spacing:.26em; text-transform:uppercase; color:var(--slate);
  margin:0 0 .8rem; }
.lead { font-size:1.12rem; line-height:1.75; max-width:46rem; }

table.tl { width:100%; border-collapse:collapse; font-size:.92rem; }
table.tl td { border-top:1px solid var(--line); padding:1.1rem .8rem 1.1rem 0; vertical-align:top; }
table.tl td.p { width:150px; color:var(--slate); font-size:.78rem; letter-spacing:.08em; white-space:nowrap; }
table.tl .org { font-weight:500; }
table.tl .role { color:var(--bronze); font-size:.85rem; }
table.tl ul { margin:.5rem 0 0 1rem; padding:0; line-height:1.6; }

.card { border:1px solid var(--line); background:#FBFAF8; padding:1.5rem; height:100%; margin-bottom:1rem; }
.card h4 { font-family:'Cormorant Garamond',serif; font-weight:500; font-size:1.35rem; margin:0 0 1rem; }
.card dl { display:grid; grid-template-columns:90px 1fr; gap:.45rem .8rem; margin:0; font-size:.86rem; }
.card dt { font-size:.62rem; letter-spacing:.2em; text-transform:uppercase; color:var(--slate); padding-top:.2rem; }
.card dd { margin:0; }

.frame img { border:1px solid var(--line); padding:6px; background:#fff; }
.list { list-style:none; padding:0; margin:0; font-size:.9rem; }
.list li { border-top:1px solid var(--line); padding:.65rem 0; }
.list li small { display:block; color:var(--slate); font-size:.78rem; }
.chips span { display:inline-block; border:1px solid var(--line); padding:.3rem .7rem;
  margin:0 .4rem .5rem 0; font-size:.78rem; }

.stButton button, .stDownloadButton button, .stFormSubmitButton button, .stLinkButton a {
  border-radius:0 !important; border:1px solid var(--ink) !important; background:transparent !important;
  color:var(--ink) !important; letter-spacing:.2em; text-transform:uppercase; font-size:.7rem !important; }
.stButton button:hover, .stDownloadButton button:hover, .stFormSubmitButton button:hover,
.stLinkButton a:hover { background:var(--ink) !important; color:var(--bg) !important; }
.stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div {
  border-radius:0 !important; background:#fff !important; }
[data-testid="stForm"] { border:1px solid var(--line); border-radius:0; padding:2rem; }
.st-key-hp_website { position:absolute !important; left:-10000px !important; height:0; overflow:hidden; }
.foot { border-top:1px solid var(--line); margin-top:4rem; padding-top:1.2rem; font-size:.7rem;
  letter-spacing:.2em; text-transform:uppercase; color:var(--slate); display:flex; justify-content:space-between; }
</style>
"""


def section(num: str, title: str, anchor: str) -> None:
    st.markdown(f'<div class="sec" id="{anchor}"><span>{num} /</span>{esc(title)}</div>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------- sections
def render_nav(p: dict) -> None:
    name = esc(p.get("identity", {}).get("full_name"))
    st.markdown(
        f"""<div class="topnav"><div class="topnav-inner"><div class="mark">{name}</div><nav>
        <a href="#profile">Profile</a><a href="#works">Works</a>
        <a href="#credentials">Credentials</a><a href="#contact">Contact</a></nav></div></div>""",
        unsafe_allow_html=True)


def render_hero(p: dict, headshot: Path | None) -> None:
    ident, contact = p.get("identity", {}), p.get("contact", {})
    left, right = st.columns([3, 1], gap="large")
    with left:
        meta = " · ".join(x for x in (ident.get("headline"), ident.get("credentials"), ident.get("location")) if x)
        st.markdown(f'<div class="hero-name">{esc(ident.get("full_name"))}</div>'
                    f'<div class="hero-meta">{esc(meta)}</div>', unsafe_allow_html=True)
        st.write("")
        b1, b2, _ = st.columns([1, 1, 2])
        cv = ROOT / (contact.get("cv_file") or "Profile.pdf")
        if cv.exists():
            b1.download_button("Download CV", cv.read_bytes(), file_name=f"{cv.stem}.pdf",
                               mime="application/pdf", width="stretch")
        if contact.get("linkedin"):
            b2.link_button("LinkedIn", contact["linkedin"], width="stretch")
    with right:
        if headshot:
            st.markdown('<div class="frame">', unsafe_allow_html=True)
            st.image(Image.open(headshot), width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="hero-rule"></div>', unsafe_allow_html=True)


def render_profile(p: dict) -> None:
    section("01", "Profile", "profile")
    ident = p.get("identity", {})
    a, b = st.columns([2, 1], gap="large")
    with a:
        st.markdown(f'<p class="lead">{esc(ident.get("summary"))}</p>', unsafe_allow_html=True)
        if ident.get("philosophy"):
            st.markdown(f'<p class="label" style="margin-top:2rem">Approach</p>'
                        f'<p>{esc(ident["philosophy"])}</p>', unsafe_allow_html=True)
    with b:
        rows = "".join(
            f'<li>{esc(i["country"])}<small>{esc(i.get("field"))} · {esc(i.get("period"))}</small></li>'
            for i in p.get("international_experience", []))
        if rows:
            st.markdown(f'<p class="label">International Experience</p><ul class="list">{rows}</ul>',
                        unsafe_allow_html=True)


def spec_card(pr: dict) -> str:
    fields = [("Client", pr.get("client")), ("Role", pr.get("role")),
              ("Location", pr.get("location")), ("Scope", pr.get("scope"))]
    dl = "".join(f"<dt>{k}</dt><dd>{esc(v)}</dd>" for k, v in fields if v)
    return f'<div class="card"><h4>{esc(pr.get("title"))}</h4><dl>{dl}</dl></div>'


def render_works(p: dict, gallery: list[Path]) -> None:
    section("02", "Selected Works & Experience", "works")
    if gallery:
        st.markdown('<p class="label">Gallery</p>', unsafe_allow_html=True)
        cols = st.columns(3, gap="medium")
        for i, img in enumerate(gallery):
            with cols[i % 3]:
                st.markdown('<div class="frame">', unsafe_allow_html=True)
                st.image(Image.open(img), caption=caption_from(img), width="stretch")
                st.markdown("</div>", unsafe_allow_html=True)
    projects = p.get("projects", [])
    if projects:
        st.markdown('<p class="label" style="margin-top:1.5rem">Projects</p>', unsafe_allow_html=True)
        cols = st.columns(2, gap="medium")
        for i, pr in enumerate(projects):
            cols[i % 2].markdown(spec_card(pr), unsafe_allow_html=True)

    rows = []
    for e in p.get("experience", []):
        bullets = "".join(f"<li>{esc(h)}</li>" for h in e.get("highlights") or [])
        role = f'<div class="role">{esc(e["role"])}</div>' if e.get("role") else ""
        loc = f'<div class="role" style="color:#5E6670">{esc(e["location"])}</div>' if e.get("location") else ""
        rows.append(f'<tr><td class="p">{esc(e.get("period"))}</td><td><div class="org">'
                    f'{esc(e.get("organisation"))}</div>{role}{loc}'
                    f'{"<ul>" + bullets + "</ul>" if bullets else ""}</td></tr>')
    if rows:
        st.markdown('<p class="label" style="margin-top:2.5rem">Career Timeline</p>'
                    f'<table class="tl">{"".join(rows)}</table>', unsafe_allow_html=True)


def render_credentials(p: dict) -> None:
    section("03", "Credentials & Capabilities", "credentials")
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        items = "".join(f'<li>{esc(e["degree"])}<small>{esc(e.get("institution"))}'
                        f'{" · " + esc(e["period"]) if e.get("period") else ""}</small></li>'
                        for e in p.get("education", []))
        st.markdown(f'<p class="label">Education</p><ul class="list">{items}</ul>', unsafe_allow_html=True)
        items = "".join(f'<li>{esc(c["name"])}<small>{esc(c.get("issuer"))}'
                        f'{" · " + esc(c["date"]) if c.get("date") else ""}</small></li>'
                        for c in p.get("certifications", []))
        st.markdown(f'<p class="label" style="margin-top:2rem">Licences & Certifications</p>'
                    f'<ul class="list">{items}</ul>', unsafe_allow_html=True)
    with c2:
        skills = p.get("skills", {})
        for key, label in (("core", "Core Competencies"), ("technical", "Technical / CAD / BIM"),
                           ("systems", "Systems")):
            if skills.get(key):
                chips = "".join(f"<span>{esc(s)}</span>" for s in skills[key])
                st.markdown(f'<p class="label">{label}</p><div class="chips">{chips}</div><br>',
                            unsafe_allow_html=True)
    with c3:
        items = "".join(f'<li>{esc(l["language"])}{"<small>" + esc(l["level"]) + "</small>" if l.get("level") else ""}</li>'
                        for l in p.get("languages", []))
        st.markdown(f'<p class="label">Languages</p><ul class="list">{items}</ul>', unsafe_allow_html=True)


@st.cache_resource
def supabase_client():
    url, key = get_secret("SUPABASE_URL"), get_secret("SUPABASE_KEY")
    if not url or not key:
        return None
    from supabase import create_client
    return create_client(url, key)


def save_inquiry(row: dict) -> None:
    client = supabase_client()
    if client is None:
        raise RuntimeError("Supabase credentials are not configured.")
    # returning="minimal": anon has INSERT only, so it must not ask for the row back.
    client.table("portfolio_inquiries").insert(row, returning="minimal").execute()


def render_contact(p: dict) -> None:
    section("04", "Inquiries & Contact", "contact")
    contact = p.get("contact", {})
    info, form = st.columns([1, 2], gap="large")
    with info:
        lines = [("Email", contact.get("email"), f'mailto:{contact.get("email")}'),
                 ("Phone", contact.get("phone"), f'tel:{re.sub(r"[^0-9+]", "", contact.get("phone") or "")}'),
                 ("LinkedIn", "linkedin.com/in/damir-hadzic-sa71000" if contact.get("linkedin") else "",
                  contact.get("linkedin")),
                 ("Based in", p.get("identity", {}).get("location"), None)]
        html_lines = ""
        for label, value, href in lines:
            if not value:
                continue
            shown = f'<a href="{esc(href)}" target="_blank">{esc(value)}</a>' if href else esc(value)
            html_lines += f"<li><small>{label}</small>{shown}</li>"
        st.markdown(f'<ul class="list">{html_lines}</ul>', unsafe_allow_html=True)

    with form:
        if st.session_state.get("sent"):
            st.markdown('<p class="lead">Thank you. Your inquiry has been received and '
                        'will be answered personally.</p>', unsafe_allow_html=True)
            if st.button("Send another inquiry"):
                st.session_state.sent = False
                st.rerun()
            return
        with st.form("inquiry", clear_on_submit=False, border=True):
            a, b = st.columns(2)
            name = a.text_input("Name")
            email = b.text_input("Email")
            kind = st.selectbox("Inquiry type", p.get("inquiry_types") or ["General"])
            message = st.text_area("Message", height=160, max_chars=5000)
            honeypot = st.text_input("Website", key="hp_website", label_visibility="collapsed")
            submitted = st.form_submit_button("Send inquiry")

        if not submitted:
            return
        name, email, message = name.strip(), email.strip(), message.strip()
        if honeypot:  # bot filled the hidden field: pretend success, store nothing
            st.session_state.sent = True
            st.rerun()
        errors = []
        if not 2 <= len(name) <= 120:
            errors.append("Please enter your name.")
        if not EMAIL_RE.match(email) or len(email) > 254:
            errors.append("Please enter a valid email address.")
        if len(message) < 10:
            errors.append("Please write a message of at least 10 characters.")
        if time.time() - st.session_state.get("last_sent", 0) < SUBMIT_COOLDOWN_S:
            errors.append("Please wait a minute before sending another inquiry.")
        if errors:
            for e in errors:
                st.warning(e)
            return
        try:
            save_inquiry({"sender_name": name, "sender_email": email,
                          "project_type": kind, "message": message})
        except Exception:
            st.error("The message could not be sent right now. Please use the email address shown.")
            return
        st.session_state.last_sent = time.time()
        st.session_state.sent = True
        st.rerun()


# ---------------------------------------------------------------- main
def main() -> None:
    profile = load_profile()
    headshot, gallery = scan_assets()
    st.markdown(CSS, unsafe_allow_html=True)
    render_nav(profile)
    render_hero(profile, headshot)
    render_profile(profile)
    render_works(profile, gallery)
    render_credentials(profile)
    render_contact(profile)
    name = esc(profile.get("identity", {}).get("full_name"))
    st.markdown(f'<div class="foot"><span>© {time.strftime("%Y")} {name}</span>'
                f'<span>Sarajevo</span></div>', unsafe_allow_html=True)


main()
