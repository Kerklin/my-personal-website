# my-personal-website

Minimal architectural portfolio for **Damir Hadžić**, built with Streamlit. Visitor inquiries are stored privately in Supabase.

```
app.py                  Streamlit app (layout, CSS, contact form)
profile_data.yaml       ALL content: edit this, not app.py
.streamlit/config.toml  Theme
requirements.txt
.gitignore              Keeps secrets.toml and .env out of GitHub
Profile.pdf             Your LinkedIn PDF (add it: enables "Download CV")
assets/                 Optional images (headshot.jpg + project photos)
```

## 1. Supabase setup (once)

Supabase dashboard > your project > **SQL Editor** > New query > paste > **Run**:

```sql
create table if not exists public.portfolio_inquiries (
  id           uuid primary key default gen_random_uuid(),
  created_at   timestamptz not null default now(),
  sender_name  text not null,
  sender_email text not null,
  project_type text,
  message      text not null,
  is_read      boolean not null default false
);

alter table public.portfolio_inquiries enable row level security;

-- anon may only INSERT; no SELECT / UPDATE / DELETE for the public
revoke all on public.portfolio_inquiries from anon, authenticated;
grant insert on public.portfolio_inquiries to anon;

drop policy if exists "anon_insert_only" on public.portfolio_inquiries;
create policy "anon_insert_only" on public.portfolio_inquiries
  for insert to anon
  with check (
    is_read = false
    and char_length(sender_name)  between 2 and 120
    and char_length(sender_email) between 5 and 254
    and char_length(message)      between 10 and 5000
  );
```

No SELECT policy exists, so the public cannot read messages. You read them in **Table Editor** (you are logged in as owner).

Using Claude Code with the Supabase MCP instead? Prompt: *"Find my active Supabase project, run the SQL in README.md section 1, then print the Project URL and anon key."*

Credentials: **Project Settings > API** (or **Data API**): copy **Project URL** and the **anon / publishable** key. Never use the `service_role` key here.

## 2. Local secrets (never committed)

`.streamlit/secrets.toml`
```toml
SUPABASE_URL = "https://YOUR-PROJECT-REF.supabase.co"
SUPABASE_KEY = "YOUR-ANON-KEY"
```

`.env` (backup)
```
SUPABASE_URL=https://YOUR-PROJECT-REF.supabase.co
SUPABASE_KEY=YOUR-ANON-KEY
```

## 3. Run on Windows

```powershell
cd my-personal-website
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:PYTHONUTF8=1
streamlit run app.py
```

Opens at http://localhost:8501. Send one test inquiry, check it in Supabase **Table Editor**, then delete it:

```sql
delete from public.portfolio_inquiries where sender_email = 'test@example.com';
```

## 4. Push to GitHub

```powershell
git init
git add .
git status          # secrets.toml and .env must NOT be listed
git commit -m "Initial portfolio"
gh repo create my-personal-website --public --source=. --push
```

If either secret file appears in `git status`: `git rm --cached .streamlit/secrets.toml .env`, then commit again.

## 5. Deploy on Streamlit Community Cloud

1. share.streamlit.io > **Create app** > repo `my-personal-website`, branch `main`, file `app.py`.
2. **Advanced settings > Secrets** (or later **App settings > Secrets**), paste:

```toml
SUPABASE_URL = "https://YOUR-PROJECT-REF.supabase.co"
SUPABASE_KEY = "YOUR-ANON-KEY"
```

3. Deploy.

## Updating content

- Text, jobs, projects, education: edit `profile_data.yaml`. Empty values (`""`, `[]`) are hidden automatically.
- Headshot: `assets/headshot.jpg` (any filename containing headshot, portrait, profile or photo).
- Project photos: any `.jpg/.png/.webp` in `assets/`. Caption = filename (`preschool_tuzla_after.jpg` shows "Preschool Tuzla After").
- No images: projects are shown as specification cards.

## Form protection

Input validation, hidden honeypot field (bots are silently ignored), 60-second resubmit cooldown per session, and database-side length checks in the RLS policy.
