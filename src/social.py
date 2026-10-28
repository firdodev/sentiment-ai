"""Lexon komentet nga një link posti: Instagram (post, reel), Facebook, LinkedIn, TikTok.

Dy mënyra lidhjeje (çelësat ruhen në .env, kurrë në frontend):
  1. Apify (APIFY_TOKEN): funksionon me postime publike në të katër platformat.
  2. Meta Graph API (META_ACCESS_TOKEN + FB_PAGE_ID / IG_USER_ID): API zyrtare,
     por vetëm për postimet e faqes / llogarisë suaj.
API-të zyrtare të LinkedIn dhe TikTok kërkojnë miratim të veçantë nga platforma,
prandaj për to përdoret Apify.
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

MAX_COMMENTS = 1000
LABELS = {"instagram": "Instagram", "facebook": "Facebook", "linkedin": "LinkedIn", "tiktok": "TikTok"}
_HOSTS = {
    "instagram": ("instagram.com", "instagr.am"),
    "facebook": ("facebook.com", "fb.com", "fb.watch"),
    "linkedin": ("linkedin.com", "lnkd.in"),
    "tiktok": ("tiktok.com",),
}
_TRACKING = re.compile(r"^(utm_|igsh|igshid|si$|mibextid|rdid|share_|_r$|_t$|is_from_webapp|sender_device)")


class SocialError(Exception):
    def __init__(self, message, code="gabim", help=None, status=400):
        super().__init__(message)
        self.message, self.code, self.help, self.status = message, code, help, status

    def to_dict(self):
        return {"gabim": self.message, "kodi": self.code, "ndihme": self.help}


# ---------- Leximi i linkut ----------
def parse_url(raw: str) -> dict:
    url = (raw or "").strip()
    if not url:
        raise SocialError("Vendos linkun e postimit.")
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    for prefix in ("www.", "m.", "web.", "mobile."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    platform = next((p for p, hosts in _HOSTS.items()
                     if any(host == h or host.endswith("." + h) for h in hosts)), None)
    if not platform:
        raise SocialError("Platforma nuk mbështetet. Përdor një link nga Instagram, Facebook, "
                          "LinkedIn ose TikTok.", code="platforme_e_panjohur")

    path = parts.path.rstrip("/")
    query = urllib.parse.parse_qs(parts.query)
    kind, ident = "post", None

    if platform == "instagram":
        share = re.match(r"/share/(?:(p|reel)/)?([A-Za-z0-9_-]+)", path)
        m = re.search(r"/(p|reel|reels|tv)/([A-Za-z0-9_-]+)", path)
        if share:  # linqet "Shpërndaj": kodi s'është shortcode; Apify e ridrejton te posti i vërtetë
            kind = "reel" if share.group(1) == "reel" else "post"
            url = f"https://www.instagram.com{parts.path}"
        elif m:
            kind = "reel" if m.group(1) in ("reel", "reels", "tv") else "post"
            ident = m.group(2)
            url = f"https://www.instagram.com/{'reel' if kind == 'reel' else 'p'}/{ident}/"
        else:
            raise SocialError("Linku i Instagram duhet të jetë një post ose reel "
                              "(p.sh. instagram.com/p/... ose instagram.com/reel/...).")
    elif platform == "tiktok":
        m = re.search(r"/(video|photo)/(\d+)", path)
        kind = "video"
        if m:
            ident = m.group(2)
        elif not host.startswith(("vm.", "vt.")) and "/t/" not in path:
            raise SocialError("Linku i TikTok duhet të jetë një video (tiktok.com/@perdoruesi/video/...).")
    elif platform == "linkedin":
        m = re.search(r"activity[-:](\d{10,})", path) or re.search(r"urn:li:(?:share|ugcPost):(\d{10,})", path)
        ident = m.group(1) if m else None
        if not ident and host != "lnkd.in":
            raise SocialError("Linku i LinkedIn duhet të jetë një postim (linkedin.com/posts/... "
                              "ose linkedin.com/feed/update/urn:li:activity:...).")
    elif platform == "facebook":
        if "story_fbid" in query:
            ident = query["story_fbid"][0]
        elif "fbid" in query:
            ident, kind = query["fbid"][0], "foto"
        elif "v" in query:
            ident, kind = query["v"][0], "video"
        else:
            m = re.search(r"/(posts|videos|reel|share/[prv])/([A-Za-z0-9_-]+)", path)
            if m:
                ident = m.group(2)
                kind = {"videos": "video", "reel": "reel"}.get(m.group(1), "post")
            elif host != "fb.watch":
                raise SocialError("Linku i Facebook duhet të jetë një postim, video ose reel.")

    if platform != "instagram":  # hiq parametrat e gjurmimit, mbaj ata që identifikojnë postin
        clean_q = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if not _TRACKING.match(k)]
        url = urllib.parse.urlunsplit(("https", parts.netloc, parts.path,
                                       urllib.parse.urlencode(clean_q), ""))
    return {"platforma": platform, "emri": LABELS[platform], "lloji": kind, "id": ident, "url": url}


# ---------- HTTP ----------
def _request(url, data=None, headers=None, timeout=60):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json",
                                                           **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read())
        except Exception:
            detail = {}
        raise _HttpError(exc.code, detail) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SocialError(f"Nuk u lidh me shërbimin: {getattr(exc, 'reason', exc)}",
                          code="rrjeti", status=502) from exc


class _HttpError(Exception):
    def __init__(self, status, detail):
        super().__init__(status)
        self.status, self.detail = status, detail


# ---------- Apify ----------
FREE_PLAN_IG_COMMENTS = 15  # plani falas i Apify kthen vetëm faqen e parë të komenteve


def _ig_input(url, n, actor):
    if actor.endswith("instagram-scraper"):  # actor-i i përgjithshëm: zgjidh llojin "comments"
        return {"directUrls": [url], "resultsType": "comments", "resultsLimit": n, "addParentData": False}
    return {"directUrls": [url], "resultsLimit": n, "includeNestedComments": False}  # instagram-comment-scraper


ACTORS = {  # platforma: (actor i paracaktuar, ndërtuesi i input-it)
    "instagram": ("apify~instagram-scraper", _ig_input),
    "facebook": ("apify~facebook-comments-scraper",
                 lambda url, n, _: {"startUrls": [{"url": url}], "resultsLimit": n,
                                    "includeNestedComments": False}),
    "tiktok": ("clockworks~tiktok-comments-scraper",
               lambda url, n, _: {"postURLs": [url], "commentsPerPost": n, "maxRepliesPerComment": 0}),
    "linkedin": ("harvestapi~linkedin-post-comments",
                 lambda url, n, _: {"posts": [url], "maxItems": n, "scrapeReplies": False}),
}


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _normalize_item(platform, item) -> dict | None:
    if not isinstance(item, dict) or item.get("error"):
        return None
    if platform == "linkedin":
        actor = item.get("actor") or {}
        text, author, date = item.get("commentary"), actor.get("name"), item.get("createdAt")
        likes = sum(_int(r.get("count")) for r in item.get("reactionTypeCounts") or [])
    elif platform == "tiktok":
        text, author, date, likes = (item.get("text"), item.get("uniqueId"),
                                     item.get("createTimeISO"), _int(item.get("diggCount")))
    elif platform == "facebook":
        text, author, date, likes = (item.get("text"), item.get("profileName"),
                                     item.get("date"), _int(item.get("likesCount")))
    else:
        text, author, date, likes = (item.get("text"), item.get("ownerUsername"),
                                     item.get("timestamp"), _int(item.get("likesCount")))
    if not text or not str(text).strip():
        return None
    return {"koment": str(text).strip(), "autori": author or "", "data": date or "", "pelqime": likes}


def fetch_apify(info: dict, limit: int) -> list[dict]:
    token = os.environ.get("APIFY_TOKEN")
    platform = info["platforma"]
    default_actor, build = ACTORS[platform]
    actor = os.environ.get(f"APIFY_{platform.upper()}_ACTOR", default_actor).replace("/", "~")
    endpoint = (f"https://api.apify.com/v2/acts/{urllib.parse.quote(actor, safe='~')}"
                "/run-sync-get-dataset-items?timeout=240&format=json&clean=true")
    try:
        items = _request(endpoint, build(info["url"], limit, actor),
                         {"Authorization": f"Bearer {token}"}, timeout=300)
    except _HttpError as exc:
        msg = (exc.detail.get("error") or {}).get("message", "") if isinstance(exc.detail, dict) else ""
        hints = {401: "Token-i i Apify nuk është i vlefshëm.",
                 402: "Llogaria Apify nuk ka kredit të mjaftueshëm.",
                 403: "Apify nuk e lejon këtë veprim me këtë token.",
                 404: f"Actor-i '{actor}' nuk u gjet në Apify.",
                 408: "Leximi zgjati shumë. Provo me më pak komente."}
        raise SocialError(hints.get(exc.status, f"Apify ktheu gabim {exc.status}. {msg}").strip(),
                          code="apify", status=502) from exc
    items = items if isinstance(items, list) else []
    comments = [c for c in (_normalize_item(platform, it) for it in items) if c]
    if not comments:
        errors = [it.get("error") or it.get("errorDescription") for it in items
                  if isinstance(it, dict) and (it.get("error") or it.get("errorDescription"))]
        detail = f" ({errors[0]})" if errors else ""
        raise SocialError(f"Nuk u gjet asnjë koment publik në këtë postim{detail}. "
                          "Kontrollo që postimi është publik dhe ka komente.", code="pa_komente",
                          status=404)
    return comments[:limit]


# ---------- Meta Graph API (zyrtare, për faqen / llogarinë tuaj) ----------
def _graph_base():
    return f"https://graph.facebook.com/{os.environ.get('META_GRAPH_VERSION', 'v23.0')}"


def _graph(path_or_url, params=None):
    if path_or_url.startswith("https://"):
        url = path_or_url
    else:
        q = urllib.parse.urlencode({**(params or {}), "access_token": os.environ["META_ACCESS_TOKEN"]})
        url = f"{_graph_base()}/{path_or_url}?{q}"
    try:
        return _request(url, timeout=30)
    except _HttpError as exc:
        msg = (exc.detail.get("error") or {}).get("message", f"HTTP {exc.status}")
        raise SocialError(f"Meta Graph API: {msg}", code="meta", status=502) from exc


def _pages(first, max_items):
    data = _graph(*first)
    while True:
        for item in data.get("data", []):
            yield item
            max_items -= 1
            if max_items <= 0:
                return
        nxt = (data.get("paging") or {}).get("next")
        if not nxt:
            return
        data = _graph(nxt)


def fetch_meta(info: dict, limit: int) -> list[dict]:
    platform = info["platforma"]
    if platform == "instagram":
        user = os.environ["IG_USER_ID"]
        media_id = next((m["id"] for m in _pages((f"{user}/media", {"fields": "id,shortcode", "limit": 100}), 2000)
                         if m.get("shortcode") == info["id"]), None)
        if not media_id:
            raise SocialError("Ky post nuk u gjet në llogarinë tuaj Instagram. Graph API lexon "
                              "vetëm postimet e llogarisë që lidhët.", code="jo_i_juaji", status=404)
        rows = _pages((f"{media_id}/comments", {"fields": "id,text,timestamp,username,like_count",
                                               "limit": 100}), limit)
        return [{"koment": r.get("text", ""), "autori": r.get("username", ""), "data": r.get("timestamp", ""),
                 "pelqime": _int(r.get("like_count"))} for r in rows if r.get("text")]

    page = os.environ["FB_PAGE_ID"]
    post_id = None
    if info["id"] and info["id"].isdigit():
        post_id = f"{page}_{info['id']}"
    else:
        needle = info["id"] or urllib.parse.urlsplit(info["url"]).path.rstrip("/")
        for p in _pages((f"{page}/posts", {"fields": "id,permalink_url", "limit": 100}), 600):
            if needle and needle in (p.get("permalink_url") or ""):
                post_id = p["id"]
                break
    if not post_id:
        raise SocialError("Ky postim nuk u gjet në faqen tuaj Facebook.", code="jo_i_juaji", status=404)
    rows = _pages((f"{post_id}/comments", {"fields": "id,message,created_time,from,like_count",
                                          "filter": "stream", "limit": 100}), limit)
    return [{"koment": r.get("message", ""), "autori": (r.get("from") or {}).get("name", ""),
             "data": r.get("created_time", ""), "pelqime": _int(r.get("like_count"))}
            for r in rows if r.get("message")]


# ---------- Zgjedhja e burimit ----------
def providers_for(platform: str) -> list[str]:
    out = []
    if os.environ.get("META_ACCESS_TOKEN") and (
            (platform == "instagram" and os.environ.get("IG_USER_ID")) or
            (platform == "facebook" and os.environ.get("FB_PAGE_ID"))):
        out.append("meta")
    if os.environ.get("APIFY_TOKEN"):
        out.append("apify")
    return out


def setup_help(platform: str) -> list[str]:
    steps = ["Krijo një llogari falas në apify.com dhe kopjo API token-in "
             "(Settings, API & Integrations).",
             "Vendose te paneli \"Lidhjet\" si APIFY_TOKEN. Funksionon për postime publike."]
    if platform in ("instagram", "facebook"):
        steps.append("Alternativë zyrtare për faqen tuaj: META_ACCESS_TOKEN + "
                     + ("IG_USER_ID (llogari Instagram Business)." if platform == "instagram"
                        else "FB_PAGE_ID (token i faqes me leje pages_read_user_content)."))
    else:
        steps.append(f"API zyrtare e {LABELS[platform]} kërkon miratim të veçantë nga platforma, "
                     "prandaj këtu përdoret Apify.")
    return steps


def fetch_comments(raw_url: str, limit=200, provider: str | None = None) -> dict:
    info = parse_url(raw_url)
    limit = max(1, min(int(limit or 200), MAX_COMMENTS))
    available = providers_for(info["platforma"])
    if provider:
        available = [p for p in available if p == provider]
    if not available:
        raise SocialError(f"Nuk ka asnjë lidhje të konfiguruar për {info['emri']}.",
                          code="pa_konfigurim", help=setup_help(info["platforma"]), status=400)
    last_error = None
    for p in available:
        try:
            comments = fetch_meta(info, limit) if p == "meta" else fetch_apify(info, limit)
            result = {"posti": info, "burimi": p, "komente": comments, "numri": len(comments)}
            if (p == "apify" and info["platforma"] == "instagram"
                    and len(comments) <= FREE_PLAN_IG_COMMENTS < limit):
                result["shenim"] = (f"U lexuan vetëm {len(comments)} komente. Plani falas i Apify kthen "
                                    "rreth 15 komente për postim; planet me pagesë i lexojnë të gjitha.")
            return result
        except SocialError as exc:  # p.sh. posti s'është i juaji në Meta -> provo Apify
            last_error = exc
    raise last_error
