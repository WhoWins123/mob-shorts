# Mob Battle Shorts Bot

Makes and posts a Minecraft "mob vs mob - who wins?" YouTube Short **3 times a day**, all by itself,
on GitHub's free servers. Your PC can be off.

Each video:
- picks a fresh, fair matchup: *6 Overworld Mobs vs 6 Nether Mobs*, *10 Zombies vs 3 Piglin Brutes*, *Undead vs Illagers*...
- simulates the fight with real mob stats (melee, arrows, fireballs, creeper explosions)
- draws the mobs with the real textures from Minecraft's game files (downloaded from Mojang)
- adds an AI voiceover ("Six Overworld mobs versus six Nether mobs. Who wins?" ... "The Nether mobs win!"),
  original chiptune music and sound effects
- uploads it as a Short with title, description and hashtags

You do the setup below **once** (about 20 minutes). You never give your password to anyone - Google
just asks you to click "Allow".

---

## 1. Make the YouTube channel

Go to **youtube.com**, sign in with your Gmail, click your picture → **Create a channel**.
Give it a name and picture.

## 2. Put the bot on GitHub

1. Make a free account at **github.com**.
2. Click **+ → New repository**. Name it `mob-shorts`. **Public** is easiest (unlimited free
   run time). Private also works. Click **Create repository**.
3. On the new repo page click **uploading an existing file**. Drag **everything inside** the unzipped
   `mob-shorts` folder into the page, including the `.github` folder. Click **Commit changes**.
   - Can't see `.github`? In File Explorer: **View → Show → Hidden items**.

## 3. Let the bot upload to your channel (Google Cloud, free)

1. Go to **console.cloud.google.com** and sign in with the same Gmail.
2. Top bar → project picker → **New project** → name it `mob-shorts` → **Create**, then select it.
3. Search bar → **YouTube Data API v3** → **Enable**.
4. Search bar → **Google Auth Platform** (or "OAuth consent screen") → **Get started**:
   - App name `mob-shorts`, support email = your Gmail → Next
   - Audience: **External** → Next → contact email = your Gmail → Finish → **Create**
5. Left menu **Audience** → **Publish app** → Confirm.
   (Important: if you skip this, the login stops working after 7 days.)
6. Left menu **Clients** → **Create client**:
   - Type: **Web application**
   - Under **Authorized redirect URIs** click **Add URI** and paste
     `https://developers.google.com/oauthplayground`
   - **Create**. Copy the **Client ID** and **Client secret** somewhere for a minute.

## 4. Get your upload key (refresh token)

1. Open **https://developers.google.com/oauthplayground**
2. Click the **gear** (top right) → tick **Use your own OAuth credentials** → paste the Client ID and
   Client secret → close the box.
3. In the left box **"Input your own scopes"** paste:
   `https://www.googleapis.com/auth/youtube.upload` → **Authorize APIs**.
4. Pick your Gmail. You'll see **"Google hasn't verified this app"** - that's normal, it's your own
   app: click **Advanced → Go to mob-shorts (unsafe)** → **Continue / Allow**.
   If asked which account/channel, choose your new channel.
5. Click **Exchange authorization code for tokens**. Copy the **Refresh token**.

## 5. Give the keys to GitHub (kept secret)

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**. Add 3:

| Name | Value |
|---|---|
| `YT_CLIENT_ID` | the Client ID |
| `YT_CLIENT_SECRET` | the Client secret |
| `YT_REFRESH_TOKEN` | the Refresh token |

## 6. Test it, then let it run

1. Repo → **Actions** tab → if asked, click **I understand my workflows, enable them**.
2. Click **Make and post a Short** → **Run workflow** (leave "Upload to YouTube" **off**) → **Run**.
3. After ~3-5 minutes open the finished run → scroll to **Artifacts** → download the video and watch it.
4. Happy? Run it again with **Upload to YouTube** ticked - it posts to your channel.

From then on it posts by itself around **9:23am, 2:23pm and 6:23pm** (Pacific). GitHub sometimes starts
scheduled runs 5-30 minutes late; that's normal.

---

## Changing things

- **Post privately first:** Settings → Secrets and variables → Actions → **Variables** tab →
  New variable `YT_PRIVACY` = `private` (or `unlisted`). Delete it to go public.
- **Different times / more or fewer posts:** edit the `cron` lines in `.github/workflows/shorts.yml`
  (times are UTC).
- **Pause it:** Actions → Make and post a Short → **⋯ → Disable workflow**.
- Each run's video is kept for 7 days under the run's **Artifacts**.

## Good to know

- YouTube doesn't pay for "mass-produced or repetitive" content. Lots of near-identical template videos
  with an AI voice can get turned down for monetization, even if they get views. Posting is fine.
- Mob textures come straight from Mojang's game files when the bot runs, like any gameplay video.
  If a Minecraft update moves a texture, that mob is just skipped until it's fixed.
- If a mob ever looks scrambled in a video, its sprite layout needs a tweak in `bot/mobs.py`.
