"""
Public Menu Page — /menu/{outlet_id}
No authentication required.
Returns a beautifully styled HTML menu page for customers to browse.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse
from app.database import supabase

router = APIRouter(prefix="/menu", tags=["Public Menu"])


@router.get("/{outlet_id}", response_class=HTMLResponse)
async def get_public_menu(outlet_id: str):
    """
    Public endpoint — returns an HTML menu page for the given outlet.
    Customers scan the QR code and land here to browse the menu.
    """

    # ── 1. Fetch outlet details ───────────────────────────────────────────
    outlet_resp = supabase.table("single_outlets").select(
        "outlet_name, address, city, state, pincode, owner_phone, outlet_type, is_active"
    ).eq("id", outlet_id).execute()

    if not outlet_resp.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found for this outlet."
        )

    outlet = outlet_resp.data[0]

    if not outlet.get("is_active", False):
        return HTMLResponse(
            content=_render_inactive_page(outlet.get("outlet_name", "Restaurant")),
            status_code=200,
        )

    # ── 2. Fetch available menu items ─────────────────────────────────────
    items_resp = supabase.table("kds_menu_items").select(
        "id, item_name, description, price, is_veg, is_available, category_id"
    ).eq("outlet_id", outlet_id).eq("is_available", True).order("item_name").execute()

    items = items_resp.data or []

    # ── 3. Fetch active categories ────────────────────────────────────────
    cats_resp = supabase.table("kds_menu_categories").select(
        "id, name, display_order"
    ).eq("is_active", True).order("display_order").execute()

    categories = cats_resp.data or []

    # ── 4. Group items by category ────────────────────────────────────────
    cat_map = {c["id"]: c["name"] for c in categories}
    grouped: dict[str, list] = {}
    uncategorized: list = []

    for item in items:
        cid = item.get("category_id")
        if cid and cid in cat_map:
            grouped.setdefault(cid, []).append(item)
        else:
            uncategorized.append(item)

    # Build ordered list: (category_name, [items])
    sections: list[tuple[str, list]] = []
    for cat in categories:
        cat_items = grouped.get(cat["id"], [])
        if cat_items:
            sections.append((cat["name"], cat_items))
    if uncategorized:
        sections.append(("Other Items", uncategorized))

    # ── 5. Render HTML ────────────────────────────────────────────────────
    return HTMLResponse(
        content=_render_menu_page(outlet, sections, len(items)),
        status_code=200,
    )


# ── HTML Renderers ────────────────────────────────────────────────────────────

def _build_address(outlet: dict) -> str:
    parts = [
        outlet.get("address") or "",
        outlet.get("city") or "",
        outlet.get("state") or "",
        outlet.get("pincode") or "",
    ]
    return ", ".join(p.strip() for p in parts if p.strip())


def _render_menu_page(outlet: dict, sections: list, total_items: int) -> str:
    outlet_name = outlet.get("outlet_name", "Restaurant")
    address = _build_address(outlet)
    phone = outlet.get("owner_phone") or ""
    outlet_type = (outlet.get("outlet_type") or "").replace("_", " ").title()

    # ── Veg / non-veg counts ──────────────────────────────────────────────────
    total_veg = sum(
        1 for _, cat_items in sections
        for item in cat_items if item.get("is_veg", True)
    )
    total_nonveg = total_items - total_veg

    # ── Build nav pills + sections HTML ──────────────────────────────────────
    nav_html = ""
    sections_html = ""

    for i, (cat_name, items) in enumerate(sections):
        cat_id = f"sec-{i}"
        nav_html += (
            f'<a href="#{cat_id}" class="cat-pill">'
            f'{_esc(cat_name)}'
            f'<span class="pill-count">{len(items)}</span>'
            f'</a>\n'
        )

        rows_html = ""
        for item in items:
            name = item.get("item_name", "")
            desc = item.get("description") or ""
            price = float(item.get("price", 0))
            is_veg = item.get("is_veg", True)

            price_str = f"₹{int(price)}" if price == int(price) else f"₹{price:.2f}"
            dot_color = "#2e7d32" if is_veg else "#c62828"
            dot_title = "Vegetarian" if is_veg else "Non-Vegetarian"
            desc_html = f'<p class="item-desc">{_esc(desc)}</p>' if desc else ""

            rows_html += f"""
            <div class="menu-item">
              <div class="veg-indicator" title="{dot_title}">
                <div class="veg-outer" style="border-color:{dot_color};">
                  <div class="veg-inner" style="background:{dot_color};"></div>
                </div>
              </div>
              <div class="item-info">
                <span class="item-name">{_esc(name)}</span>
                {desc_html}
              </div>
              <span class="item-price">{price_str}</span>
            </div>"""

        sections_html += f"""
        <div class="category-block" id="{cat_id}">
          <div class="category-header">
            <h3 class="category-name">{_esc(cat_name)}</h3>
            <span class="cat-count">{len(items)}</span>
          </div>
          <div class="items-list">{rows_html}</div>
        </div>"""

    # ── HTML components ───────────────────────────────────────────────────────
    address_html = f'<p class="outlet-address">📍 {_esc(address)}</p>' if address else ""
    phone_html = f'<p class="outlet-phone">📞 {_esc(phone)}</p>' if phone else ""
    type_badge = f'<span class="type-badge">{_esc(outlet_type)}</span>' if outlet_type else ""
    nav_section = f'<nav class="cat-nav" aria-label="Menu categories">{nav_html}</nav>' if nav_html else ""

    veg_stat_html = f"""
      <div class="stat-sep"></div>
      <div class="stat-item">
        <span class="stat-val" style="color:#2e7d32">{total_veg}</span>
        <span class="stat-label">Veg</span>
      </div>
      <div class="stat-sep"></div>
      <div class="stat-item">
        <span class="stat-val" style="color:#c62828">{total_nonveg}</span>
        <span class="stat-label">Non-Veg</span>
      </div>""" if total_items > 0 else ""

    stats_html = f"""
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-val">{total_items}</span>
        <span class="stat-label">Items</span>
      </div>
      {veg_stat_html}
    </div>""" if total_items > 0 else ""

    empty_html = ""
    if total_items == 0:
        empty_html = (
            '<div class="empty-msg">'
            '<span class="empty-icon">🍽️</span>'
            '<p>Our menu is being prepared.</p>'
            '<p class="empty-sub">Please check back in a few minutes!</p>'
            '</div>'
        )

    # Search bar (only if there are items)
    search_html = ""
    if total_items > 0:
        search_html = (
            '<div class="search-bar">'
            '<input type="text" class="search-input" placeholder="Search menu items..." '
            'id="menuSearch" autocomplete="off" />'
            '</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="theme-color" content="#7b1d1d" />
  <meta name="description" content="Browse the menu of {_esc(outlet_name)}" />
  <title>{_esc(outlet_name)} — Menu</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    /* ── Reset ────────────────────────────────────────────────────────── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #f7f2ee;
      color: #1a1a1a;
      min-height: 100vh;
      padding-bottom: 44px;
    }}

    /* ── Header ───────────────────────────────────────────────────────── */
    .header {{
      background: linear-gradient(150deg, #6b1515 0%, #7b1d1d 45%, #9e2b2b 100%);
      color: #fff;
      padding: 32px 20px 36px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }}
    .header::before {{
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(
        105deg,
        transparent 40%,
        rgba(255,255,255,0.05) 45%,
        rgba(255,255,255,0.08) 50%,
        rgba(255,255,255,0.05) 55%,
        transparent 60%
      );
      animation: shimmer 6s ease-in-out infinite;
      pointer-events: none;
    }}
    @keyframes shimmer {{
      0% {{ transform: translateX(-100%); }}
      100% {{ transform: translateX(100%); }}
    }}
    .header::after {{
      content: '';
      position: absolute;
      bottom: -1px;
      left: 0; right: 0;
      height: 24px;
      background: #f7f2ee;
      border-radius: 50% 50% 0 0 / 24px 24px 0 0;
    }}
    .header-brand {{
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 3px;
      text-transform: uppercase;
      color: rgba(255,255,255,0.5);
      margin-bottom: 12px;
    }}
    .outlet-name {{
      font-family: 'Playfair Display', Georgia, serif;
      font-size: clamp(26px, 7vw, 42px);
      font-weight: 800;
      line-height: 1.1;
      letter-spacing: -0.5px;
      margin-bottom: 12px;
      text-shadow: 0 2px 12px rgba(0,0,0,0.25);
    }}
    .outlet-meta {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 5px;
    }}
    .outlet-address, .outlet-phone {{
      font-size: 12.5px;
      color: rgba(255,255,255,0.75);
      display: flex;
      align-items: center;
      gap: 5px;
    }}
    .type-badge {{
      display: inline-flex;
      align-items: center;
      margin-top: 10px;
      padding: 4px 14px;
      background: rgba(255,255,255,0.15);
      border: 1px solid rgba(255,255,255,0.3);
      border-radius: 20px;
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 1px;
      text-transform: uppercase;
    }}

    /* ── Stats bar ────────────────────────────────────────────────────── */
    .stats-bar {{
      display: flex;
      align-items: center;
      justify-content: center;
      background: #fff;
      padding: 14px 20px;
      border-bottom: 1px solid #ede8e2;
      box-shadow: 0 1px 0 #ede8e2;
    }}
    .stat-item {{
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 0 20px;
    }}
    .stat-val {{
      font-size: 20px;
      font-weight: 700;
      color: #7b1d1d;
      line-height: 1;
    }}
    .stat-label {{
      font-size: 10px;
      font-weight: 600;
      color: #aaa;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-top: 3px;
    }}
    .stat-sep {{
      width: 1px;
      height: 30px;
      background: #ede8e2;
    }}

    /* ── Category nav ─────────────────────────────────────────────────── */
    .cat-nav {{
      display: flex;
      gap: 8px;
      padding: 12px 14px;
      overflow-x: auto;
      scrollbar-width: none;
      -webkit-overflow-scrolling: touch;
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(247,242,238,0.96);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-bottom: 1px solid rgba(0,0,0,0.06);
      box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    }}
    .cat-nav::-webkit-scrollbar {{ display: none; }}
    .cat-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
      padding: 9px 16px;
      background: #fff;
      border: 1.5px solid #e2dbd5;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 600;
      color: #555;
      text-decoration: none;
      transition: all 0.2s ease;
      white-space: nowrap;
    }}
    .cat-pill:hover, .cat-pill.active {{
      background: #7b1d1d;
      border-color: #7b1d1d;
      color: #fff;
    }}
    .cat-pill:hover .pill-count, .cat-pill.active .pill-count {{
      background: rgba(255,255,255,0.25);
      color: #fff;
    }}
    .cat-pill:active {{
      transform: scale(0.95);
    }}
    .pill-count {{
      background: #f0ebe5;
      color: #7b1d1d;
      font-size: 10px;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 10px;
      min-width: 18px;
      text-align: center;
      transition: background 0.18s ease, color 0.18s ease;
    }}

    /* ── Search bar ───────────────────────────────────────────────────── */
    .search-bar {{
      position: sticky;
      top: 50px;
      z-index: 99;
      padding: 8px 14px 10px;
      background: rgba(247,242,238,0.96);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
    }}
    .search-input {{
      width: 100%;
      padding: 11px 14px 11px 40px;
      border: 1.5px solid #e2dbd5;
      border-radius: 12px;
      font-size: 14px;
      font-family: 'Inter', sans-serif;
      background: #fff;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23aaa' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: 13px center;
      background-size: 16px;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
      color: #1a1a1a;
    }}
    .search-input:focus {{
      border-color: #7b1d1d;
      box-shadow: 0 0 0 3px rgba(123,29,29,0.1);
    }}
    .search-input::placeholder {{
      color: #bbb;
    }}
    .no-results {{
      text-align: center;
      padding: 40px 24px;
      color: #aaa;
      font-size: 14px;
      display: none;
    }}

    /* ── Content ──────────────────────────────────────────────────────── */
    .content {{
      max-width: 720px;
      margin: 0 auto;
      padding: 18px 12px 52px;
    }}

    /* ── Category block ───────────────────────────────────────────────── */
    .category-block {{
      margin-bottom: 16px;
      background: #fff;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 6px 20px rgba(0,0,0,0.06);
      scroll-margin-top: 110px;
      opacity: 0;
      transform: translateY(20px);
      transition: opacity 0.5s ease, transform 0.5s ease;
    }}
    .category-block.visible {{
      opacity: 1;
      transform: translateY(0);
    }}
    .category-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 18px;
      border-left: 4px solid #7b1d1d;
      background: linear-gradient(to right, #fdf5f5, #fff);
      border-bottom: 1px solid #f5ecea;
    }}
    .category-name {{
      font-size: 15px;
      font-weight: 700;
      color: #7b1d1d;
      letter-spacing: 0.2px;
    }}
    .cat-count {{
      background: #7b1d1d;
      color: #fff;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 9px;
      border-radius: 10px;
      min-width: 22px;
      text-align: center;
    }}
    .items-list {{ padding: 4px 0; }}

    /* ── Menu item ────────────────────────────────────────────────────── */
    .menu-item {{
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 15px 18px;
      min-height: 56px;
      border-bottom: 1px solid #f7f2ee;
      transition: background 0.15s ease, transform 0.1s ease;
    }}
    .menu-item:last-child {{ border-bottom: none; }}
    .menu-item:hover {{ background: #fdf9f7; }}
    .menu-item:active {{
      transform: scale(0.99);
      background: #f5eeea;
    }}

    .veg-indicator {{ flex-shrink: 0; margin-top: 3px; }}
    .veg-outer {{
      width: 17px; height: 17px;
      border: 2px solid;
      border-radius: 3px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .veg-inner {{ width: 8px; height: 8px; border-radius: 50%; }}

    .item-info {{ flex: 1; min-width: 0; }}
    .item-name {{
      font-size: 14.5px;
      font-weight: 600;
      color: #1a1a1a;
      display: block;
      line-height: 1.35;
    }}
    .item-desc {{
      font-size: 11.5px;
      color: #aaa;
      margin-top: 3px;
      line-height: 1.45;
    }}
    .item-price {{
      flex-shrink: 0;
      background: #7b1d1d;
      color: #fff;
      font-size: 13px;
      font-weight: 700;
      padding: 5px 13px;
      border-radius: 20px;
      white-space: nowrap;
      align-self: center;
      transition: transform 0.15s ease;
    }}
    .menu-item:hover .item-price {{
      transform: scale(1.05);
    }}

    /* ── Empty state ──────────────────────────────────────────────────── */
    .empty-msg {{
      text-align: center;
      padding: 80px 24px;
      animation: fadeIn 0.6s ease;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(16px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .empty-icon {{
      font-size: 64px;
      display: block;
      margin-bottom: 20px;
      animation: pulse 2s ease-in-out infinite;
    }}
    @keyframes pulse {{
      0%, 100% {{ transform: scale(1); }}
      50% {{ transform: scale(1.08); }}
    }}
    .empty-msg p {{ font-size: 16px; color: #999; line-height: 1.8; }}
    .empty-msg .empty-sub {{ font-size: 13px; color: #c0b8b0; margin-top: 8px; }}

    /* ── Back to top button ───────────────────────────────────────────── */
    .back-to-top {{
      position: fixed;
      bottom: 60px;
      right: 20px;
      width: 44px;
      height: 44px;
      background: #7b1d1d;
      color: #fff;
      border: none;
      border-radius: 50%;
      font-size: 20px;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(123,29,29,0.35);
      opacity: 0;
      transform: scale(0.8);
      transition: opacity 0.3s, transform 0.3s;
      z-index: 200;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .back-to-top.show {{
      opacity: 1;
      transform: scale(1);
    }}
    .back-to-top:active {{
      transform: scale(0.92);
    }}

    /* ── Footer ───────────────────────────────────────────────────────── */
    .footer {{
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      text-align: center;
      padding: 10px 16px;
      font-size: 11px;
      color: #a09890;
      background: rgba(247,242,238,0.95);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      border-top: 1px solid rgba(0,0,0,0.06);
      z-index: 50;
    }}
    .footer a {{ color: #7b1d1d; text-decoration: none; font-weight: 600; }}
    .footer a:hover {{ text-decoration: underline; }}

    /* ── Responsive ───────────────────────────────────────────────────── */
    @media (max-width: 480px) {{
      .outlet-name {{ font-size: 26px; }}
      .stat-val {{ font-size: 17px; }}
      .stat-item {{ padding: 0 14px; }}
      .search-bar {{ top: 48px; }}
      .category-block {{ scroll-margin-top: 105px; }}
    }}
  </style>
</head>
<body>

  <!-- Header -->
  <header class="header">
    <p class="header-brand">Khanoos KDS</p>
    <h1 class="outlet-name">{_esc(outlet_name)}</h1>
    <div class="outlet-meta">
      {address_html}
      {phone_html}
    </div>
    {type_badge}
  </header>

  <!-- Stats bar -->
  {stats_html}

  <!-- Category navigation -->
  {nav_section}

  <!-- Search bar -->
  {search_html}

  <!-- Menu content -->
  <main class="content">
    {sections_html if sections_html else empty_html}
    <div class="no-results" id="noResults">No items found matching your search.</div>
  </main>

  <!-- Back to top -->
  <button class="back-to-top" id="backToTop" aria-label="Back to top">&uarr;</button>

  <!-- Footer -->
  <footer class="footer">
    <p>Powered by <a href="https://khanoos.com" target="_blank">Khanoos KDS</a>
       &nbsp;·&nbsp; Khanoos Enterprises 2026</p>
  </footer>

  <script>
  (function() {{
    // ── Search filtering ──────────────────────────────────────────────
    var searchEl = document.getElementById('menuSearch');
    var noResults = document.getElementById('noResults');
    if (searchEl) {{
      searchEl.addEventListener('input', function(e) {{
        var q = e.target.value.toLowerCase().trim();
        var anyVisible = false;
        document.querySelectorAll('.menu-item').forEach(function(item) {{
          var name = item.querySelector('.item-name').textContent.toLowerCase();
          var descEl = item.querySelector('.item-desc');
          var desc = descEl ? descEl.textContent.toLowerCase() : '';
          var match = q === '' || name.indexOf(q) !== -1 || desc.indexOf(q) !== -1;
          item.style.display = match ? '' : 'none';
          if (match) anyVisible = true;
        }});
        document.querySelectorAll('.category-block').forEach(function(block) {{
          var visItems = block.querySelectorAll('.menu-item');
          var hasVisible = false;
          visItems.forEach(function(it) {{ if (it.style.display !== 'none') hasVisible = true; }});
          block.style.display = (hasVisible || q === '') ? '' : 'none';
        }});
        if (noResults) noResults.style.display = (!anyVisible && q !== '') ? 'block' : 'none';
      }});
    }}

    // ── Active category pill on scroll ────────────────────────────────
    var pills = document.querySelectorAll('.cat-pill');
    var sections = document.querySelectorAll('.category-block');
    if (sections.length > 0 && 'IntersectionObserver' in window) {{
      var pillObserver = new IntersectionObserver(function(entries) {{
        entries.forEach(function(entry) {{
          if (entry.isIntersecting) {{
            var id = entry.target.id;
            pills.forEach(function(p) {{
              p.classList.toggle('active', p.getAttribute('href') === '#' + id);
            }});
            var active = document.querySelector('.cat-pill.active');
            if (active) active.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
          }}
        }});
      }}, {{ rootMargin: '-60px 0px -70% 0px', threshold: 0 }});
      sections.forEach(function(s) {{ pillObserver.observe(s); }});
    }}

    // ── Fade-in animation on scroll ───────────────────────────────────
    if ('IntersectionObserver' in window) {{
      var fadeObserver = new IntersectionObserver(function(entries) {{
        entries.forEach(function(entry) {{
          if (entry.isIntersecting) {{
            entry.target.classList.add('visible');
            fadeObserver.unobserve(entry.target);
          }}
        }});
      }}, {{ threshold: 0.1 }});
      sections.forEach(function(s) {{ fadeObserver.observe(s); }});
    }} else {{
      sections.forEach(function(s) {{ s.classList.add('visible'); }});
    }}

    // ── Back to top button ────────────────────────────────────────────
    var btn = document.getElementById('backToTop');
    if (btn) {{
      window.addEventListener('scroll', function() {{
        btn.classList.toggle('show', window.scrollY > 400);
      }});
      btn.addEventListener('click', function() {{
        window.scrollTo({{ top: 0, behavior: 'smooth' }});
      }});
    }}
  }})();
  </script>

</body>
</html>"""


def _render_inactive_page(outlet_name: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>{_esc(outlet_name)}</title>
  <style>
    body{{font-family:sans-serif;background:#f5f0eb;display:flex;align-items:center;
         justify-content:center;min-height:100vh;margin:0;}}
    .box{{text-align:center;padding:40px 24px;background:#fff;border-radius:16px;
          box-shadow:0 4px 16px rgba(0,0,0,0.1);max-width:360px;}}
    h2{{color:#7b1d1d;margin-bottom:12px;}}
    p{{color:#666;font-size:14px;}}
  </style>
</head>
<body>
  <div class="box">
    <h2>{_esc(outlet_name)}</h2>
    <p>This menu is currently unavailable.<br>Please try again later.</p>
  </div>
</body>
</html>"""


def _esc(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))
