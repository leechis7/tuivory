#pragma once
namespace tuivory {
namespace popup_detail {
inline void number(int v, int limit = 1000000) {
  if (v < 0 || v > limit)
    throw std::invalid_argument("invalid popup bounds/options");
}
inline void rect(Rect r) {
  number(r.x, 1000000000);
  number(r.y, 1000000000);
  number(r.width);
  number(r.height);
}
} // namespace popup_detail
struct PopupLayout {
  Rect bounds, card, shadow;
  std::vector<Rect> shadow_regions() const {
    auto s = shadow, c = card;
    int sr = s.x + s.width, sb = s.y + s.height, cr = c.x + c.width,
        cb = c.y + c.height, x = std::max(s.x, cr), y = std::max(s.y, cb);
    return {{x, s.y, std::max(0, sr - x), std::max(0, std::min(sb, cb) - s.y)},
            {s.x, y, s.width, std::max(0, sb - y)}};
  }
  bool hit(int x, int y) const { return card.contains(x, y); }
};
struct ShadowOptions {
  std::string mode = "off";
  int offset_x = 0, offset_y = 0;
  std::pair<int, int> offsets() const {
    if (mode != "off" && mode != "auto" && mode != "solid" && mode != "dim")
      throw std::invalid_argument("invalid shadow mode");
    popup_detail::number(offset_x);
    popup_detail::number(offset_y);
    return mode == "off"            ? std::pair<int, int>{0, 0}
           : !offset_x && !offset_y ? std::pair<int, int>{1, 1}
                                    : std::pair<int, int>{offset_x, offset_y};
  }
  PopupLayout layout(Rect bounds) const;
};
namespace popup_detail {
inline PopupLayout layout(ShadowOptions o, Rect bounds) {
  auto offsets = o.offsets();
  if (!bounds.width || !bounds.height)
    return {bounds, bounds, {}};
  int dx = std::min(offsets.first, bounds.width - 1),
      dy = std::min(offsets.second, bounds.height - 1);
  Rect card = {bounds.x, bounds.y, bounds.width - dx, bounds.height - dy},
       shadow;
  if (dx || dy) {
    bool caps = (o.mode == "auto" || o.mode == "solid") && dy > 0;
    shadow = {bounds.x + dx, bounds.y + dy - (int)caps, card.width,
              card.height + (int)caps};
  }
  return {bounds, card, shadow};
}
inline unsigned shade(unsigned backdrop, bool has_rgb, bool has_256) {
  auto rgb = color_rgb(backdrop);
  int r = rgb[0], g = rgb[1], b = rgb[2], maximum = std::max({r, g, b});
  if (maximum <= 16)
    return has_rgb ? 0x1404040 : has_256 ? 238 : 7;
  int factor = maximum <= 96 ? 2 : 4;
  if (has_rgb)
    return 0x1000000 | ((r * factor / 5) << 16) | ((g * factor / 5) << 8) |
           (b * factor / 5);
  if (has_256)
    return 232 +
           std::max(0, std::min(23, ((r + g + b) * factor / 15 - 3) / 10));
  return 0;
}
inline void paint(Canvas &canvas, Rect region, PopupLayout layout,
                  const ShadowOptions &o, bool ascii, bool has_rgb,
                  bool has_256) {
  int left = std::max(0, region.x),
      right = std::min(canvas.width, region.x + region.width),
      top = std::max(0, region.y),
      bottom = std::min(canvas.height, region.y + region.height);
  if (left >= right || top >= bottom)
    return;
  canvas.clear_cursor(Rect{left, top, right - left, bottom - top});
  for (int y = top; y < bottom; y++) {
    std::vector<unsigned> backgrounds;
    auto &row = canvas.data[y];
    for (int x = left; x < right; x++)
      backgrounds.push_back(row[x].owner >= 0
                                ? row[row[x].owner].style.background
                                : row[x].style.background);
    if (row[left].owner >= 0)
      canvas.write_style(left, y, " ", row[left].style, 1);
    int end = right - 1, start = row[end].owner >= 0 ? row[end].owner : end;
    if (end + 1 < canvas.width && row[end + 1].owner == start)
      canvas.write_style(end, y, " ", row[end].style, 1);
    for (int x = left; x < right; x++) {
      if (o.mode == "dim") {
        row[x].style.dim = true;
        continue;
      }
      unsigned bg = backgrounds[x - left],
               color = o.mode == "solid" ? 0 : shade(bg, has_rgb, has_256);
      std::string symbol = " ";
      Style style{color, color, false, false, false};
      if (ascii) {
        symbol = ".";
        style.background = bg;
      } else if (layout.shadow.height > layout.card.height) {
        if (y == layout.shadow.y) {
          symbol = "▄";
          style.background = bg;
        } else if (y == layout.shadow.y + layout.shadow.height - 1) {
          symbol = "▀";
          style.background = bg;
        }
      }
      canvas.write_style(x, y, symbol, style, 1);
    }
  }
}
} // namespace popup_detail
inline PopupLayout ShadowOptions::layout(Rect bounds) const {
  popup_detail::rect(bounds);
  return popup_detail::layout(*this, bounds);
}
inline PopupLayout popup_placement(Rect anchor, Rect viewport, int width,
                                   int height, ShadowOptions options = {}) {
  popup_detail::rect(anchor);
  popup_detail::rect(viewport);
  popup_detail::number(width);
  popup_detail::number(height);
  auto offsets = options.offsets();
  int w = width && height ? std::min(width + offsets.first, viewport.width) : 0,
      h = width && height ? std::min(height + offsets.second, viewport.height)
                          : 0,
      mx = viewport.x + viewport.width - w,
      my = viewport.y + viewport.height - h,
      x = std::max(viewport.x, std::min(anchor.x, mx)),
      y = anchor.y + anchor.height;
  if (y > my)
    y = std::max(0, anchor.y - h);
  return popup_detail::layout(options,
                              {x, std::max(viewport.y, std::min(y, my)), w, h});
}
struct Shadow {
  ShadowOptions options;
  explicit Shadow(ShadowOptions o = {}) : options(std::move(o)) {}
  PopupLayout draw(Canvas &canvas, Rect bounds,
                   const std::function<void(Canvas &)> &painter,
                   bool ascii = false) const {
    popup_detail::rect(bounds);
    auto o = options;
    o.offsets();
    int x = std::min(bounds.x, canvas.width),
        y = std::min(bounds.y, canvas.height),
        right = std::min(canvas.width, bounds.x + bounds.width),
        bottom = std::min(canvas.height, bounds.y + bounds.height);
    auto layout = popup_detail::layout(
        o, {x, y, std::max(0, right - x), std::max(0, bottom - y)});
    Canvas working(canvas.width, canvas.height, canvas.palette,
                   canvas.surface_role);
    working.blit(canvas, {0, 0, canvas.width, canvas.height}, 0, 0);
    bool has_rgb = false, has_256 = false;
    for (const char *role : detail::tui_roles) {
      auto s = canvas.palette.style(role);
      for (auto color : {s.foreground, s.background}) {
        has_rgb = has_rgb || (color & 0x1000000);
        has_256 =
            has_256 || (!(color & 0x1000000) && color >= 16 && color <= 255);
      }
    }
    if (o.mode != "off")
      for (auto region : layout.shadow_regions())
        popup_detail::paint(working, region, layout, o, ascii, has_rgb,
                            has_256);
    auto card = layout.card;
    Canvas child(card.width, card.height, canvas.palette, canvas.surface_role);
    child.blit(working, card, 0, 0);
    child.clear_cursor();
    painter(child);
    working.blit(child, {0, 0, card.width, card.height}, card.x, card.y);
    canvas.blit(working, {0, 0, canvas.width, canvas.height}, 0, 0);
    return layout;
  }
};
} // namespace tuivory
