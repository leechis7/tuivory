package io.tuivory;

import java.util.*;
import java.util.regex.Pattern;

/** Independent Java 17 component models and terminal-cell drawing. No JNI. */
public final class Tuivory {
  private Tuivory() {}
  private static final Pattern GRAPHEME = Pattern.compile("\\X");
  private static boolean inRanges(int cp, int[][] ranges) {
    int lo = 0, hi = ranges.length - 1;
    while (lo <= hi) {
      int m = (lo + hi) >>> 1;
      if (cp < ranges[m][0])
        hi = m - 1;
      else if (cp > ranges[m][1])
        lo = m + 1;
      else
        return true;
    }
    return false;
  }
  public static List<String> graphemes(String text) {
    var out = new ArrayList<String>();
    var matcher = GRAPHEME.matcher(text);
    while (matcher.find()) out.add(matcher.group());
    return out;
  }
  public static String clean(String text) {
    return text.replaceAll("[\\x00-\\x1f\\x7f-\\x9f]", " ");
  }
  private static int clusterWidth(String g) {
    int[] points = g.codePoints().toArray();
    int total = 0, cluster = 0, base = -1, lastWidth = 0;
    boolean available = false, virama = false;
    for (int i = 0; i < points.length; i++) {
      int cp = points[i];
      if (cp == 0x200d) {
        if (!virama && i + 1 < points.length) {
          i++;
          lastWidth = 0;
        }
        continue;
      }
      if (cp == 0xfe0f && available) {
        if (inRanges(base, Data.VS16))
          cluster = 2;
        available = false;
        continue;
      }
      if (cp == 0xfe0e && available) {
        if (lastWidth == 2 && inRanges(base, Data.VS15))
          total--;
        available = false;
        continue;
      }
      if (cp >= 0x1f1e6 && cp <= 0x1f1ff) {
        int count = 0;
        for (int j = i - 1; j >= 0 && points[j] >= 0x1f1e6 && points[j] <= 0x1f1ff; j--) count++;
        if (count % 2 == 1) {
          base = cp;
          continue;
        }
      } else if (cp >= 0x1f3fb && cp <= 0x1f3ff && inRanges(base, Data.PICTOGRAPHIC))
        continue;
      int w = inRanges(cp, Data.ZERO) ? 0 : inRanges(cp, Data.WIDE) ? 2 : 1;
      if (w > 0) {
        if (virama)
          cluster = 2;
        else {
          total += cluster;
          cluster = w;
        }
        base = cp;
        lastWidth = w;
        available = true;
        virama = false;
      } else if (inRanges(cp, Data.VIRAMA))
        virama = true;
      else if (available && inRanges(cp, Data.SPACING_MC)) {
        cluster = 2;
        available = false;
        virama = false;
      } else
        virama = false;
    }
    return total + cluster;
  }
  public static int cells(String text) {
    int n = 0;
    for (String g : graphemes(clean(text))) n += clusterWidth(g);
    return n;
  }
  public static String clip(String text, int width, boolean ellipsis) {
    text = clean(text);
    if (width <= 0)
      return "";
    if (cells(text) <= width)
      return text;
    var out = new StringBuilder();
    int used = 0;
    for (String g : graphemes(text)) {
      int n = clusterWidth(g);
      if (used + n > width - (ellipsis ? 1 : 0))
        break;
      out.append(g);
      used += n;
    }
    if (ellipsis)
      out.append('~');
    return out.toString();
  }
  public record Rect(int x, int y, int width, int height) {
    public boolean contains(int px, int py) {
      return px >= x && px < x + width && py >= y && py < y + height;
    }
  }
  public record Event(String kind, String id, String text) {
    public Event() {
      this("", "", "");
    }
    public Event(String kind, String id) {
      this(kind, id, "");
    }
  }
  public static final class State {
    public boolean disabled, readOnly, busy, selected, edited, invalid;
    public boolean focusable() {
      return !disabled;
    }
    public boolean activatable() {
      return !disabled && !busy;
    }
    public boolean editable() {
      return activatable() && !readOnly;
    }
    public String role() {
      return disabled ? "disabled"
          : invalid   ? "error"
          : selected  ? "selection"
          : edited    ? "edited"
                      : "body";
    }
    public String markers() {
      return (disabled ? "-" : "") + (invalid ? "!" : "") + (selected ? ">" : "")
          + (edited ? "*" : "") + (busy ? "~" : "") + (readOnly ? "=" : "");
    }
  }
  public record Style(int foreground, int background, boolean bold, boolean dim, boolean underline,
      boolean italic) {
    public Style(int foreground, int background, boolean bold, boolean dim, boolean underline) {
      this(foreground, background, bold, dim, underline, false);
    }
    private String color(int c, boolean bg) {
      String base = bg ? "48" : "38";
      if ((c & 0x1000000) != 0)
        return base + ";2;" + ((c >> 16) & 255) + ";" + ((c >> 8) & 255) + ";" + (c & 255);
      return c < 8 ? "" + ((bg ? 40 : 30) + c)
          : c < 16 ? "" + ((bg ? 100 : 90) + c - 8)
                   : base + ";5;" + c;
    }
    public String sgr() {
      return "\033[0;" + color(foreground, false) + ";" + color(background, true)
          + (bold ? ";1" : "") + (dim ? ";2" : "") + (italic ? ";3" : "") + (underline ? ";4" : "")
          + "m";
    }
  }
  private static boolean plainTextRole(String role) {
    return List.of("body", "hint", "disabled", "info", "success", "warning", "error")
        .contains(role);
  }
  private static final int[][] ANSI_RGB = {{0, 0, 0}, {128, 0, 0}, {0, 128, 0}, {128, 128, 0},
      {0, 0, 128}, {128, 0, 128}, {0, 128, 128}, {192, 192, 192}, {128, 128, 128}, {255, 0, 0},
      {0, 255, 0}, {255, 255, 0}, {0, 0, 255}, {255, 0, 255}, {0, 255, 255}, {255, 255, 255}};
  private static int[] colorRGB(int color) {
    if (color < 0 || color > 0x1ffffff)
      throw new IllegalArgumentException("invalid color");
    if ((color & 0x1000000) != 0)
      return new int[] {(color >> 16) & 255, (color >> 8) & 255, color & 255};
    if (color > 255)
      throw new IllegalArgumentException("invalid color");
    if (color < 16)
      return ANSI_RGB[color].clone();
    if (color >= 232) {
      int v = 8 + (color - 232) * 10;
      return new int[] {v, v, v};
    }
    int n = color - 16;
    int[] cube = {0, 95, 135, 175, 215, 255};
    return new int[] {cube[n / 36], cube[(n / 6) % 6], cube[n % 6]};
  }
  private static double colorLuminance(int color) {
    var rgb = colorRGB(color);
    return .2126 * Data.LUMINANCE[rgb[0]] + .7152 * Data.LUMINANCE[rgb[1]]
        + .0722 * Data.LUMINANCE[rgb[2]];
  }
  private static double colorContrast(int a, int b) {
    double x = colorLuminance(a), y = colorLuminance(b);
    return (Math.max(x, y) + .05) / (Math.min(x, y) + .05);
  }
  public static final class Palette {
    private final int theme, profile;
    public Palette() {
      this("dark", "256");
    }
    public Palette(String theme, String colors) {
      this.theme = List.of("dark", "light", "blackwhite").indexOf(theme);
      this.profile = List.of("8", "16", "256", "truecolor").indexOf(colors);
      if (this.theme < 0 || this.profile < 0)
        throw new IllegalArgumentException("unknown palette");
    }
    public Style style(String role) {
      return style(role, false);
    }
    public Style style(String role, boolean focused) {
      int index = Arrays.asList(Data.ROLES).indexOf(role);
      if (index < 0)
        throw new IllegalArgumentException("unknown role");
      int[] t =
          Data.PALETTES[(theme * 4 + profile) * Data.ROLES.length + index];
      return new Style(t[0], t[1], t[2] != 0, role.equals("disabled"), focused);
    }
    public Style textOnSurface(String role, String surface) {
      return textOnSurface(role, surface, false);
    }
    public Style textOnSurface(String role, String surface, boolean focused) {
      var text = style(role);
      var base = style(surface);
      int foreground = text.foreground;
      double current = colorContrast(foreground, base.background);
      if (current < (role.equals("disabled") ? 2 : 4.5)
          && colorContrast(base.foreground, base.background) > current)
        foreground = base.foreground;
      boolean disabled = role.equals("disabled");
      return new Style(foreground, base.background, disabled ? false : text.bold,
          text.dim || disabled, focused && !disabled);
    }
    public Style controlOnSurface(State state, String surface, boolean focused) {
      String role = state.role();
      return plainTextRole(role) ? textOnSurface(role, surface, focused && state.focusable())
                                 : style(role, focused && state.focusable());
    }
  }
  public static final class Cell {
    public String text = " ";
    public Style style;
    public int owner = -1;
    Cell(Style style) {
      this.style = style;
    }
  }
  public static final class Canvas {
    public final int width, height;
    public final Palette palette;
    public final String surfaceRole;
    public final Cell[][] data;
    public int cursorX = -1, cursorY = -1;
    private int cursorWidth = 1;
    public Canvas(int width, int height) {
      this(width, height, new Palette());
    }
    public Canvas(int width, int height, Palette palette) {
      this(width, height, palette, "surface");
    }
    public Canvas(int width, int height, Palette palette, String surface) {
      if (width < 0 || height < 0 || (long) width * height > 1_000_000)
        throw new IllegalArgumentException("invalid dimensions");
      this.width = width;
      this.height = height;
      this.palette = palette;
      this.surfaceRole = surface;
      palette.style(surface);
      data = new Cell[height][width];
      for (var row : data)
        for (int x = 0; x < width; x++) row[x] = new Cell(palette.style(surface));
    }
    private void erase(int x, int y) {
      var row = data[y];
      int start = row[x].owner >= 0 ? row[x].owner : x, end = start + 1;
      while (end < width && row[end].owner == start) end++;
      clearCursor(new Rect(start, y, end - start, 1));
      for (int i = start; i < end; i++) {
        row[i].text = " ";
        row[i].owner = -1;
      }
    }
    public void write(int x, int y, String text, String role, boolean focused, int extent) {
      String actual = role.equals("surface") ? surfaceRole : role;
      Style style = plainTextRole(role) ? palette.textOnSurface(role, surfaceRole, focused)
                                        : palette.style(actual, focused);
      writeStyle(x, y, text, style, extent);
    }
    public void writeStyle(int x, int y, String text, Style style) {
      writeStyle(x, y, text, style, width - x);
    }
    public void writeStyle(int x, int y, String text, Style style, int extent) {
      if (y < 0 || y >= height || extent < 0)
        return;
      int limit = Math.min(width, x + extent);
      for (String g : graphemes(clean(text))) {
        int n = clusterWidth(g);
        if (n == 0)
          continue;
        if (x >= limit)
          break;
        if (x < 0 || x + n > limit) {
          for (int i = Math.max(0, x); i < Math.min(limit, x + n); i++) {
            erase(i, y);
            data[y][i].style = style;
          }
          x += n;
          continue;
        }
        for (int i = x; i < x + n; i++) erase(i, y);
        data[y][x].text = g;
        data[y][x].style = style;
        for (int i = x + 1; i < x + n; i++) {
          data[y][i].text = "";
          data[y][i].style = style;
          data[y][i].owner = x;
        }
        x += n;
      }
    }
    public void write(int x, int y, String text, String role) {
      write(x, y, text, role, false, width - x);
    }
    public void fill(Rect r, String role) {
      for (int y = Math.max(0, r.y); y < Math.min(height, r.y + r.height); y++)
        write(r.x, y, " ".repeat(Math.max(0, r.width)), role, false, r.width);
    }
    public Rect panel(Rect r, String title, boolean focused, boolean ascii) {
      fill(r, "surface");
      if (r.width < 2 || r.height < 2)
        return new Rect(r.x, r.y, 0, 0);
      String[] b = ascii ? new String[] {"+", "+", "+", "+", "-", "|"}
          : focused      ? new String[] {"╔", "╗", "╚", "╝", "═", "║"}
                         : new String[] {"┌", "┐", "└", "┘", "─", "│"};
      String role = focused ? "focus.border" : "hint";
      var style = palette.textOnSurface(role, surfaceRole);
      writeStyle(r.x, r.y, b[0] + b[4].repeat(r.width - 2) + b[1], style);
      writeStyle(r.x, r.y + r.height - 1, b[2] + b[4].repeat(r.width - 2) + b[3], style);
      for (int y = r.y + 1; y < r.y + r.height - 1; y++) {
        writeStyle(r.x, y, b[5], style);
        writeStyle(r.x + r.width - 1, y, b[5], style);
      }
      writeStyle(r.x + 2, r.y, clip(title, r.width - 4, false), style);
      return new Rect(r.x + 1, r.y + 1, r.width - 2, r.height - 2);
    }
    public void setCursor(int x, int y, int glyphWidth) {
      cursorWidth = Math.max(1, glyphWidth);
      if (x >= 0 && (long) x + Math.max(1, glyphWidth) <= width && y >= 0 && y < height) {
        cursorX = x;
        cursorY = y;
      } else
        cursorX = cursorY = -1;
    }
    public void clearCursor() {
      cursorX = cursorY = -1;
    }
    public void clearCursor(Rect r) {
      if (cursorX >= 0 && r.width > 0 && r.y <= cursorY && (long) cursorY < (long) r.y + r.height
          && (long) r.x < (long) cursorX + cursorWidth && (long) cursorX < (long) r.x + r.width)
        clearCursor();
    }
    public void blit(Canvas source, Rect r, int x, int y) {
      for (int v : new int[] {r.x, r.y, r.width, r.height, x, y})
        if (v < -1000000000 || v > 1000000000)
          throw new IllegalArgumentException("invalid blit bounds");
      if (r.width < 0 || r.height < 0)
        throw new IllegalArgumentException("invalid blit bounds");
      int left = Math.max(0, Math.max(r.x, r.x - x)), top = Math.max(0, Math.max(r.y, r.y - y)),
          right =
              (int) Math.min(source.width, Math.min((long) r.x + r.width, (long) r.x + width - x)),
          bottom = (int) Math.min(
              source.height, Math.min((long) r.y + r.height, (long) r.y + height - y));
      if (left >= right || top >= bottom)
        return;
      int cx = source.cursorX, cy = source.cursorY, cw = source.cursorWidth;
      Cell[][] rows = new Cell[bottom - top][right - left];
      for (int sy = top; sy < bottom; sy++)
        for (int sx = left; sx < right; sx++) {
          var cell = source.data[sy][sx];
          int start = cell.owner >= 0 ? cell.owner : sx, end = start + 1;
          while (end < source.width && source.data[sy][end].owner == start) end++;
          var copy = new Cell(cell.style);
          if (start >= left && end <= right) {
            copy.text = cell.text;
            copy.owner = cell.owner < 0 ? -1 : x + start - r.x;
          }
          rows[sy - top][sx - left] = copy;
        }
      for (int sy = top; sy < bottom; sy++)
        for (int sx = left; sx < right; sx++) erase(x + sx - r.x, y + sy - r.y);
      for (int sy = top; sy < bottom; sy++)
        for (int sx = left; sx < right; sx++)
          data[y + sy - r.y][x + sx - r.x] = rows[sy - top][sx - left];
      if (cx >= left && cx + cw <= right && cy >= top && cy < bottom)
        setCursor(x + cx - r.x, y + cy - r.y, cw);
    }
    public List<String> lines() {
      var out = new ArrayList<String>();
      for (var row : data) {
        var line = new StringBuilder();
        for (var c : row) line.append(c.text);
        out.add(line.toString());
      }
      return out;
    }
    public String ansi() {
      var out = new StringBuilder("\033[?25l");
      for (int y = 0; y < height; y++) {
        out.append("\033[").append(y + 1).append(";1H");
        String previous = "";
        for (var c : data[y]) {
          if (c.owner >= 0)
            continue;
          String style = c.style.sgr();
          if (!style.equals(previous)) {
            out.append(style);
            previous = style;
          }
          out.append(c.text);
        }
      }
      out.append("\033[0m");
      if (cursorX >= 0)
        out.append("\033[")
            .append(cursorY + 1)
            .append(';')
            .append(cursorX + 1)
            .append("H\033[?25h");
      return out.toString();
    }
  }
  public static final class Node {
    public final String id;
    public String name, parent = "", secondary = "", icon = "", asciiIcon = "";
    public Long count;
    public boolean branch;
    public Node(String id, String name) {
      this.id = id;
      this.name = name;
    }
    public Node(String id, String name, String parent) {
      this(id, name);
      this.parent = parent;
    }
    private Node copy() {
      var n = new Node(id, name, parent);
      n.secondary = secondary;
      n.icon = icon;
      n.asciiIcon = asciiIcon;
      n.count = count;
      n.branch = branch;
      return n;
    }
  }
  public static final class Tree {
    public DropRequest requestDrop(
        String source, String target, String position, DragOptions options, DropPolicy allow) {
      return Tuivory.requestDrop(this, source, target, position, options, allow);
    }
    public DropRequest requestDrop(
        String source, String target, String position, DragOptions options) {
      return requestDrop(source, target, position, options, null);
    }
    public DropRequest requestDrop(String source, String target, String position) {
      return requestDrop(source, target, position, null, null);
    }
    public Tree applyDrop(DropRequest request) {
      return Tuivory.applyDrop(this, request);
    }
    public DropRequest keyboardDrop(String direction, DragOptions options, DropPolicy allow) {
      return Tuivory.keyboardDrop(this, direction, options, allow);
    }
    public DropRequest keyboardDrop(String direction) {
      return keyboardDrop(direction, null, null);
    }
    public List<Node> nodes() {
      return nodes.stream().map(Node::copy).toList();
    }
    private final List<Node> nodes;
    private final Map<String, Integer> depth = new HashMap<>();
    private final Set<String> branches = new HashSet<>();
    public final Set<String> expanded = new HashSet<>();
    private final Map<String, Node> byId = new HashMap<>();
    public String selected = "";
    public int scroll, horizontal;
    public Tree(List<Node> input) {
      nodes = input.stream().map(Node::copy).toList();
      var stack = new ArrayList<String>();
      for (var n : nodes) {
        if (n.id.isEmpty() || byId.put(n.id, n) != null)
          throw new IllegalArgumentException("invalid node ID");
        if (n.parent.isEmpty())
          stack.clear();
        else {
          int p = stack.indexOf(n.parent);
          if (p < 0)
            throw new IllegalArgumentException("tree requires contiguous preorder");
          stack.subList(p + 1, stack.size()).clear();
          branches.add(n.parent);
        }
        if (stack.size() > 128)
          throw new IllegalArgumentException("tree depth exceeds 128");
        depth.put(n.id, stack.size());
        stack.add(n.id);
        if (n.branch)
          branches.add(n.id);
      }
      reconcile(1);
    }
    public List<Node> visible() {
      var out = new ArrayList<Node>();
      var seen = new HashSet<String>();
      for (var n : nodes)
        if (n.parent.isEmpty() || seen.contains(n.parent) && expanded.contains(n.parent)) {
          out.add(n.copy());
          seen.add(n.id);
        }
      return out;
    }
    private List<Node> reconcile(int height) {
      expanded.retainAll(branches);
      var rows = visible();
      var ids = rows.stream().map(n -> n.id).toList();
      while (!selected.isEmpty() && !ids.contains(selected) && byId.containsKey(selected))
        selected = byId.get(selected).parent;
      if (!ids.contains(selected))
        selected = ids.isEmpty() ? "" : ids.get(0);
      int i = ids.indexOf(selected), h = Math.max(1, height);
      scroll = Math.max(0, Math.min(scroll, rows.size() - h));
      if (i >= 0) {
        if (i < scroll)
          scroll = i;
        if (i >= scroll + h)
          scroll = i - h + 1;
      }
      return rows;
    }
    public Event handle(String action, int height) {
      var rows = reconcile(height);
      if (rows.isEmpty())
        return new Event();
      String old = selected;
      int i = 0;
      while (!rows.get(i).id.equals(old)) i++;
      var node = rows.get(i);
      int target = i;
      switch (action) {
        case "up" -> target--;
        case "down" -> target++;
        case "home" -> target = 0;
        case "end" -> target = rows.size() - 1;
        case "page_up" -> target -= Math.max(1, height);
        case "page_down" -> target += Math.max(1, height);
        case "pan_left" -> horizontal = Math.max(0, horizontal - 4);
        case "pan_right" -> horizontal = Math.min(65535, horizontal + 4);
        case "activate" -> {
          return new Event("activate", old);
        }
        case "left" -> {
          if (expanded.remove(old)) {
            reconcile(height);
            return new Event("collapse", old);
          }
          if (!node.parent.isEmpty())
            selected = node.parent;
        }
        case "right", "toggle" -> {
          if (branches.contains(old)) {
            if (action.equals("toggle") && expanded.remove(old)) {
              reconcile(height);
              return new Event("collapse", old);
            }
            if (expanded.add(old)) {
              reconcile(height);
              return new Event("expand", old);
            }
            if (i + 1 < rows.size() && rows.get(i + 1).parent.equals(old))
              target++;
          }
        }
        default -> {
        }
      }
      target = Math.max(0, Math.min(rows.size() - 1, target));
      if (target != i)
        selected = rows.get(target).id;
      reconcile(height);
      return selected.equals(old) ? new Event() : new Event("select", selected);
    }
    public Event click(int x, int y, int height) {
      var rows = reconcile(height);
      if (y < 0 || y >= height || scroll + y >= rows.size())
        return new Event();
      var node = rows.get(scroll + y);
      String old = selected;
      selected = node.id;
      if (x >= 2 && x + horizontal == 2 + 2 * depth.get(node.id)) {
        var e = handle("toggle", height);
        if (!e.kind.isEmpty())
          return e;
      }
      return old.equals(selected) ? new Event() : new Event("select", selected);
    }
    public void draw(Canvas c, Rect r, boolean focused, boolean ascii) {
      c.fill(r, "surface");
      var rows = reconcile(r.height);
      for (int y = 0; y < r.height && scroll + y < rows.size(); y++) {
        var n = rows.get(scroll + y);
        boolean current = n.id.equals(selected);
        String arrow = branches.contains(n.id) ? expanded.contains(n.id) ? ascii ? "v" : "▾"
                : ascii                                                  ? ">"
                                                                         : "▸"
                                               : " ",
               icon = ascii ? n.asciiIcon : n.icon;
        String text = "  ".repeat(depth.get(n.id)) + arrow + " "
            + (icon.isEmpty() ? "" : icon + " ") + n.name
            + (n.secondary.isEmpty() ? "" : "  " + n.secondary)
            + (n.count == null ? "" : " (" + n.count + ")");
        var parts = graphemes(text);
        int start = 0, skipped = 0;
        while (start < parts.size() && skipped < horizontal) skipped += cells(parts.get(start++));
        text = String.join("", parts.subList(start, parts.size()));
        c.write(r.x, r.y + y, (current ? "> " : "  ") + clip(text, Math.max(0, r.width - 2), true),
            current ? "selection" : "body", focused && current, r.width);
      }
    }
  }
  public static final class Tab {
    public final String id;
    public String title;
    public boolean edited, closable, disabled;
    public Tab(String id, String title) {
      this.id = id;
      this.title = title;
    }
    private Tab copy() {
      var t = new Tab(id, title);
      t.edited = edited;
      t.closable = closable;
      t.disabled = disabled;
      return t;
    }
  }
  public record TabCell(String id, String text, int start, int width, boolean active,
      boolean focused, boolean disabled) {}
  public static final class Tabs {
    public DropRequest requestDrop(
        String source, String target, String position, DragOptions options, DropPolicy allow) {
      return Tuivory.requestDrop(this, source, target, position, options, allow);
    }
    public DropRequest requestDrop(
        String source, String target, String position, DragOptions options) {
      return requestDrop(source, target, position, options, null);
    }
    public DropRequest requestDrop(String source, String target, String position) {
      return requestDrop(source, target, position, null, null);
    }
    public Tabs applyDrop(DropRequest request) {
      return Tuivory.applyDrop(this, request);
    }
    public DropRequest keyboardDrop(String direction, DragOptions options, DropPolicy allow) {
      return Tuivory.keyboardDrop(this, direction, options, allow);
    }
    public DropRequest keyboardDrop(String direction) {
      return keyboardDrop(direction, null, null);
    }
    public List<Tab> items() {
      return items.stream().map(Tab::copy).toList();
    }
    private final List<Tab> items;
    public String active = "", focused = "";
    public int first;
    public Tabs(List<Tab> input) {
      var ids = new HashSet<String>();
      items = input.stream().map(Tab::copy).toList();
      for (var t : items)
        if (t.id.isEmpty() || !ids.add(t.id))
          throw new IllegalArgumentException("empty/duplicate tab ID");
      reconcile();
    }
    private List<Tab> reconcile() {
      var enabled = items.stream().filter(t -> !t.disabled).toList();
      if (enabled.stream().noneMatch(t -> t.id.equals(active)))
        active = enabled.isEmpty() ? "" : enabled.get(0).id;
      if (enabled.stream().noneMatch(t -> t.id.equals(focused)))
        focused = active;
      return enabled;
    }
    public Event handle(String action) {
      var enabled = reconcile();
      if (enabled.isEmpty())
        return new Event();
      int i = 0;
      while (!enabled.get(i).id.equals(focused)) i++;
      if (action.equals("activate")) {
        active = focused;
        return new Event("activate", active);
      }
      if (action.equals("close"))
        return enabled.get(i).closable ? new Event("close", focused) : new Event();
      int target = switch (action) {
        case "previous" -> Math.max(0, i - 1);
        case "next" -> Math.min(enabled.size() - 1, i + 1);
        case "first" -> 0;
        case "last" -> enabled.size() - 1;
        default -> i;
      };
      if (target != i) {
        focused = enabled.get(target).id;
        return new Event("focus", focused);
      }
      return new Event();
    }
    private static int itemWidth(Tab t) {
      return Math.max(6, Math.min(24, cells(t.title) + 5));
    }
    private int sum(int start, int target) {
      int w = 0;
      for (int i = start; i <= target; i++) w += itemWidth(items.get(i));
      return w;
    }
    public List<TabCell> layout(int width) {
      reconcile();
      var out = new ArrayList<TabCell>();
      if (width <= 2 || items.isEmpty())
        return out;
      int target = 0;
      for (int i = 0; i < items.size(); i++)
        if (items.get(i).id.equals(focused))
          target = i;
      first = Math.max(0, Math.min(first, target));
      while (first < target && sum(first, target) > width - 2) first++;
      while (first > 0 && sum(first - 1, target) <= width - 2) first--;
      int x = 1;
      for (int i = first; i < items.size() && x < width - 1; i++) {
        var t = items.get(i);
        int w = Math.min(itemWidth(t), width - 1 - x);
        if (w < 4 && !out.isEmpty())
          break;
        boolean a = t.id.equals(active), f = t.id.equals(focused);
        String suffix = (t.edited ? " *" : "") + (t.closable ? " x" : "");
        String text = clip((f ? ">" : " ") + (a ? "[" : " ")
                + clip(t.title, Math.max(0, w - 3 - suffix.length()), true) + suffix
                + (a ? "]" : " "),
            w, true);
        out.add(new TabCell(t.id, text, x, w, a, f, t.disabled));
        x += w;
      }
      return out;
    }
    public Event click(int x, int width) {
      var views = layout(width);
      if (x == 0 && first > 0)
        return handle("previous");
      if (width > 0 && x == width - 1 && first + views.size() < items.size())
        return handle("next");
      for (var v : views)
        if (x >= v.start && x < v.start + v.width && !v.disabled) {
          focused = v.id;
          if ((v.text.endsWith("x]") || v.text.endsWith("x "))
              && items.stream().anyMatch(t -> t.id.equals(v.id) && t.closable)
              && x == v.start + cells(v.text) - 2)
            return new Event("close", v.id);
          active = v.id;
          return new Event("activate", v.id);
        }
      return new Event();
    }
    public void draw(Canvas c, Rect r, boolean hasFocus, boolean ascii) {
      c.fill(r, "surface");
      var views = layout(r.width);
      if (first > 0)
        c.write(r.x, r.y, "<", "hint");
      if (first + views.size() < items.size() && r.width > 0)
        c.write(r.x + r.width - 1, r.y, ">", "hint");
      for (var v : views) {
        c.write(r.x + v.start, r.y, " ".repeat(v.width),
            v.disabled     ? "disabled"
                : v.active ? "selection"
                           : "body",
            hasFocus && v.focused, v.width);
        c.write(r.x + v.start, r.y, v.text,
            v.disabled     ? "disabled"
                : v.active ? "selection"
                           : "body",
            hasFocus && v.focused, v.width);
      }
    }
  }
  public record SplitLayout(int first, int divider, int second, boolean compact) {}
  public static final class Split {
    public int preferred, firstMin, secondMin;
    public Split(int firstMin, int secondMin, int preferred) {
      this.firstMin = Math.max(1, firstMin);
      this.secondMin = Math.max(1, secondMin);
      this.preferred = Math.max(0, preferred);
    }
    public SplitLayout layout(int total) {
      if (total < 0)
        throw new IllegalArgumentException("negative size");
      if ((long) total < (long) firstMin + secondMin + 1)
        return new SplitLayout(0, 0, total, true);
      int first = Math.max(
          firstMin, Math.min(total - 1 - secondMin, preferred == 0 ? (total - 1) / 2 : preferred));
      return new SplitLayout(first, 1, total - first - 1, false);
    }
    public boolean resize(int total, int position) {
      var old = layout(total);
      if (old.compact)
        return false;
      preferred = Math.max(firstMin, Math.min(total - 1 - secondMin, position));
      return preferred != old.first;
    }
  }
  public record LineRun(String text, String role, String id, int start, int width) {}
  public static final class LineLayout {
    public final List<LineRun> runs = new ArrayList<>();
    public int omitted;
    private int width;
    void add(String text, String role, String id) {
      text = clean(text);
      int w = cells(text);
      runs.add(new LineRun(text, role, id, width, w));
      width += w;
    }
    public String text() {
      var result = new StringBuilder();
      for (var r : runs) result.append(r.text);
      return result.toString();
    }
    public String hit(int x) {
      for (var r : runs)
        if (x >= r.start && x < r.start + r.width)
          return r.id;
      return "";
    }
    public void draw(Canvas c, Rect area) {
      c.fill(area, "surface");
      for (var r : runs)
        c.write(area.x + r.start, area.y, r.text, r.role, false, Math.max(0, area.width - r.start));
    }
  }
  public record PathItem(String id, String label) {}
  private static String tailCells(String text, int width) {
    if (cells(text) <= width)
      return clean(text);
    if (width <= 0)
      return "";
    var gs = graphemes(clean(text));
    int start = gs.size(), used = 0;
    while (start > 0 && used + cells(gs.get(start - 1)) <= width - 1)
      used += cells(gs.get(--start));
    return "~" + String.join("", gs.subList(start, gs.size()));
  }
  public static LineLayout breadcrumbs(List<PathItem> items, int width) {
    var out = new LineLayout();
    if (items.isEmpty() || width <= 0)
      return out;
    long full = 3L * (items.size() - 1);
    for (var p : items) full += cells(p.label);
    if (full <= width) {
      for (int i = 0; i < items.size(); i++) {
        if (i > 0)
          out.add(" / ", "hint", "");
        var p = items.get(i);
        out.add(p.label, i + 1 == items.size() ? "body" : "hint", p.id);
      }
      return out;
    }
    var last = items.get(items.size() - 1);
    String prefix = "";
    if (items.size() > 2 && cells(items.get(0).label) + 9 + cells(last.label) <= width) {
      out.add(items.get(0).label, "hint", items.get(0).id);
      prefix = " / ... / ";
    } else if (items.size() > 1 && width >= 7)
      prefix = "... / ";
    out.add(prefix, "hint", "");
    out.add(tailCells(last.label, width - out.width), "body", last.id);
    return out;
  }
  public record StatusItem(String id, String text, String role, int priority) {}
  public static LineLayout statusLine(List<StatusItem> source, int width) {
    var items = new ArrayList<>(source);
    items.sort(Comparator.comparingInt(StatusItem::priority).reversed());
    var out = new LineLayout();
    out.omitted = items.size();
    if (width <= 0)
      return out;
    int included = 0;
    for (int i = 0; i < items.size(); i++) {
      var item = items.get(i);
      int reserve = i + 1 < items.size() ? (" +" + (items.size() - i - 1)).length() : 0;
      String sep = included > 0 ? " | " : "", prefix = switch (item.role) {
        case "warning", "error" -> "! ";
        case "edited" -> "* ";
        case "success" -> "+ ";
        case "info" -> "i ";
        default -> "";
      };
      String text = prefix + clean(item.text);
      int needed = cells(sep) + cells(text);
      if (needed + reserve > width - out.width) {
        if (included > 0)
          break;
        int available = width - reserve > 0 ? width - reserve : width;
        text = available == 1 && !prefix.isEmpty() ? prefix.substring(0, 1)
                                                   : clip(text, available, true);
        sep = "";
      }
      if (!sep.isEmpty())
        out.add(sep, "hint", "");
      out.add(text, item.role.isEmpty() ? "body" : item.role, item.id);
      included++;
      if (needed + reserve > width)
        break;
    }
    out.omitted = items.size() - included;
    String marker = " +" + out.omitted;
    if (out.omitted > 0 && out.width + marker.length() <= width)
      out.add(marker, "hint", "");
    return out;
  }
  /** Literal grapheme buffer. Raw value is available only via explicit value(). */
  public static final class Text {
    private String value;
    public int cursor, anchor, scrollX, scrollY;
    public State state = new State();
    public boolean secret, multiline = true;
    private record Snapshot(String value, int cursor, int anchor) {}
    private final ArrayList<Snapshot> undo = new ArrayList<>(), redo = new ArrayList<>();
    public Text(String text) {
      value = Objects.requireNonNull(text);
      cursor = anchor = graphemes(text).size();
    }
    public String value() {
      return value;
    }
    public String display() {
      return secret ? "*".repeat(graphemes(value).size()) : value;
    }
    @Override
    public String toString() {
      return "Text[" + display() + ", cursor=" + cursor + ", anchor=" + anchor + "]";
    }
    private static boolean br(String g) {
      return g.equals("\r") || g.equals("\n") || g.equals("\r\n");
    }
    private static int chars(List<String> g, int n) {
      int out = 0;
      for (int i = 0; i < Math.min(n, g.size()); i++) out += g.get(i).length();
      return out;
    }
    public void select(int a, int c) {
      int n = graphemes(value).size();
      anchor = Math.max(0, Math.min(n, a));
      cursor = Math.max(0, Math.min(n, c));
    }
    private int byteIndex(int byteOffset) {
      var g = graphemes(value);
      int n = 0;
      for (int i = 0; i < g.size(); i++) {
        if (n == byteOffset)
          return i;
        n += g.get(i).getBytes(java.nio.charset.StandardCharsets.UTF_8).length;
      }
      if (n == byteOffset)
        return g.size();
      throw new IllegalArgumentException("offset splits a grapheme or is outside text");
    }
    public int[] selectionBytes() {
      var g = graphemes(value);
      return new int[] {value.substring(0, chars(g, Math.min(anchor, cursor)))
                            .getBytes(java.nio.charset.StandardCharsets.UTF_8)
                            .length,
          value.substring(0, chars(g, Math.max(anchor, cursor)))
              .getBytes(java.nio.charset.StandardCharsets.UTF_8)
              .length};
    }
    public void selectBytes(int a, int c) {
      int ai = byteIndex(a), ci = byteIndex(c);
      select(ai, ci);
    }
    public Event replaceBytes(int a, int b, String text) {
      if (a > b)
        throw new IllegalArgumentException("reversed byte range");
      return replace(byteIndex(a), byteIndex(b), text);
    }
    private Event replace(int a, int b, String text) {
      if (!state.editable() || a == b && text.isEmpty())
        return new Event();
      var g = graphemes(value);
      String prefix = value.substring(0, chars(g, a)) + text;
      String next = prefix + value.substring(chars(g, b));
      int offset = 0, at = 0;
      for (String c : graphemes(next)) {
        if (offset >= prefix.length())
          break;
        offset += c.length();
        at++;
      }
      undo.add(new Snapshot(value, cursor, anchor));
      if (undo.size() > 128)
        undo.remove(0);
      redo.clear();
      value = next;
      select(at, at);
      state.edited = true;
      return new Event("change", "");
    }
    private String sanitize(String s) {
      s = s.replace("\r\n", "\n").replace('\r', '\n');
      var out = new StringBuilder();
      s.codePoints().forEach(cp -> {
        if (cp == '\t')
          out.append(' ');
        else if (cp == '\n') {
          if (multiline)
            out.append('\n');
        } else if (cp >= 32 && !(cp >= 127 && cp < 160))
          out.appendCodePoint(cp);
      });
      return out.toString();
    }
    public Event handle(String action) {
      return handle(action, "");
    }
    public Event handle(String action, String text) {
      if (state.disabled)
        return new Event();
      select(anchor, cursor);
      var g = graphemes(value);
      int lo = Math.min(anchor, cursor), hi = Math.max(anchor, cursor), at = cursor, start = at,
          end = at;
      while (start > 0 && !br(g.get(start - 1))) start--;
      while (end < g.size() && !br(g.get(end))) end++;
      boolean extend = action.startsWith("select_");
      String move = extend ? action.substring(7) : action;
      int target = -1;
      if (extend && move.equals("all")) {
        select(0, g.size());
        return new Event("select", "");
      }
      if (move.equals("left"))
        target = !extend && lo != hi ? lo : Math.max(0, at - 1);
      if (move.equals("right"))
        target = !extend && lo != hi ? hi : Math.min(g.size(), at + 1);
      if (move.equals("home"))
        target = start;
      if (move.equals("end"))
        target = end;
      if (move.equals("up")) {
        int p = Math.max(0, start - 1);
        while (p > 0 && !br(g.get(p - 1))) p--;
        target = start > 0 ? Math.min(p + at - start, start - 1) : at;
      }
      if (move.equals("down")) {
        int e = Math.min(g.size(), end + 1);
        while (e < g.size() && !br(g.get(e))) e++;
        target = end < g.size() ? Math.min(end + 1 + at - start, e) : at;
      }
      if (target >= 0) {
        select(extend ? anchor : target, target);
        return new Event("select", "");
      }
      if (action.equals("copy") || action.equals("cut")) {
        if (secret || lo == hi || action.equals("cut") && !state.editable())
          return new Event();
        String copied = value.substring(chars(g, lo), chars(g, hi));
        if (action.equals("cut"))
          replace(lo, hi, "");
        return new Event(action, "", copied);
      }
      if (!state.editable())
        return new Event();
      if (action.equals("undo") || action.equals("redo")) {
        var src = action.equals("undo") ? undo : redo;
        var dst = action.equals("undo") ? redo : undo;
        if (src.isEmpty())
          return new Event();
        dst.add(new Snapshot(value, cursor, anchor));
        var previous = src.remove(src.size() - 1);
        value = previous.value;
        cursor = previous.cursor;
        anchor = previous.anchor;
        state.edited = true;
        return new Event("change", "");
      }
      String addition = "";
      if (action.equals("backspace")) {
        if (lo == hi && lo > 0)
          lo--;
      } else if (action.equals("delete")) {
        if (lo == hi && hi < g.size())
          hi++;
      } else if (action.equals("insert") || action.equals("paste") || action.equals("newline"))
        addition = sanitize(action.equals("newline") ? "\n" : text);
      else
        return new Event();
      return replace(lo, hi, addition);
    }
    private record Glyph(int index, String text) {}
    private List<List<Glyph>> rows() {
      var out = new ArrayList<List<Glyph>>();
      out.add(new ArrayList<>());
      var g = graphemes(value);
      for (int i = 0; i < g.size(); i++) {
        if (multiline && br(g.get(i)))
          out.add(new ArrayList<>());
        else
          out.get(out.size() - 1).add(new Glyph(i, secret ? "*" : g.get(i)));
      }
      return out;
    }
    public void draw(Canvas c, Rect r, boolean focused) {
      String role = state.disabled ? "disabled" : state.readOnly ? "body" : "field";
      c.fill(r, role);
      if (r.width <= 0 || r.height <= 0)
        return;
      var rs = rows();
      var raw = graphemes(value);
      int cy = 0, cx = 0, cw = 1;
      for (int i = 0; i < Math.min(cursor, raw.size()); i++)
        if (multiline && br(raw.get(i)))
          cy++;
      cy = Math.min(cy, rs.size() - 1);
      for (var g : rs.get(cy)) {
        if (g.index < cursor)
          cx += cells(g.text);
        if (g.index == cursor)
          cw = Math.max(1, cells(g.text));
      }
      scrollY = Math.max(0, Math.max(Math.min(scrollY, cy), cy - r.height + 1));
      scrollX = Math.max(0, Math.max(Math.min(scrollX, cx), cx + Math.min(cw, r.width) - r.width));
      int lo = Math.min(anchor, cursor), hi = Math.max(anchor, cursor);
      for (int y = 0; y < r.height && y + scrollY < rs.size(); y++) {
        int x = 0;
        for (var g : rs.get(y + scrollY)) {
          int n = cells(g.text), local = x - scrollX;
          if (local >= 0 && local + n <= r.width)
            c.write(r.x + local, r.y + y, g.text,
                lo <= g.index && g.index < hi ? "selection" : role, false, n);
          x += n;
        }
      }
      if (focused && state.editable() && cw <= r.width)
        c.setCursor(r.x + cx - scrollX, r.y + cy - scrollY, cw);
    }
    public Event click(int x, int y, int width, int height, boolean extend) {
      if (state.disabled || x < 0 || y < 0 || x >= width || y >= height)
        return new Event();
      var rs = rows();
      int row = Math.min(Math.max(0, scrollY + y), rs.size() - 1), target = 0;
      for (int i = 0; i < row; i++) target += rs.get(i).size() + 1;
      if (!rs.get(row).isEmpty())
        target = rs.get(row).get(rs.get(row).size() - 1).index + 1;
      int cell = 0;
      for (var g : rs.get(row)) {
        int n = cells(g.text);
        if (x + scrollX < cell + n) {
          target = g.index;
          break;
        }
        cell += n;
      }
      select(extend ? anchor : target, target);
      return new Event("select", "");
    }
  }
  public record FormOption(String id, String label, boolean disabled) {
    public FormOption(String id, String label) {
      this(id, label, false);
    }
  }
  public static final class Field {
    public String id, kind = "text", label = "", value = "", help = "", error = "", choice = "",
                      action = "", pending = "";
    public List<FormOption> options = new ArrayList<>();
    public State state = new State();
    public boolean required, checked, open;
    public int height = 3;
    public Field(String id) {
      this.id = id;
    }
    public Field(String id, String kind) {
      this.id = id;
      this.kind = kind;
    }
  }
  public record FormEvent(String kind, String id, String text, List<String> missing) {
    public FormEvent() {
      this("", "", "", List.of());
    }
    public FormEvent(String kind, String id) {
      this(kind, id, "", List.of());
    }
  }
  public record FormRow(String id, String text, String role, String option, boolean input,
      boolean focused, int sourceRow) {}
  private static State copyState(State s) {
    var o = new State();
    o.disabled = s.disabled;
    o.readOnly = s.readOnly;
    o.busy = s.busy;
    o.selected = s.selected;
    o.edited = s.edited;
    o.invalid = s.invalid;
    return o;
  }
  public static class Form {
    private final List<Field> fields = new ArrayList<>();
    private final Map<String, Text> inputs = new LinkedHashMap<>();
    private List<FormRow> hits = List.of();
    private int layoutWidth;
    public String focused = "";
    public int scroll;
    public Form(List<Field> source) {
      var ids = new HashSet<String>();
      for (Field f : source) {
        if (f.id.isEmpty() || !ids.add(f.id))
          throw new IllegalArgumentException("invalid field ID");
        if (f.open
            || !List.of("text", "textarea", "password", "button", "checkbox", "radio", "select")
                .contains(f.kind))
          throw new IllegalArgumentException("invalid kind/open select");
        var options = new HashSet<String>();
        for (var o : f.options)
          if (o.id().isEmpty() || !options.add(o.id()))
            throw new IllegalArgumentException("invalid option ID");
        if (!f.choice.isEmpty() && !options.contains(f.choice))
          throw new IllegalArgumentException("unknown choice");
        var owned = new Field(f.id, f.kind);
        owned.label = f.label;
        owned.value = f.value;
        owned.help = f.help;
        owned.error = f.error;
        owned.choice = f.choice;
        owned.action = f.action;
        owned.pending = f.pending;
        owned.options = new ArrayList<>(f.options);
        owned.state = copyState(f.state);
        owned.required = f.required;
        owned.checked = f.checked;
        owned.height = f.height;
        fields.add(owned);
        if (List.of("text", "textarea", "password").contains(f.kind)) {
          var t = new Text(f.value);
          t.secret = f.kind.equals("password");
          t.multiline = f.kind.equals("textarea");
          inputs.put(f.id, t);
          owned.value = t.display();
        }
      }
      eligible();
    }
    private Field field(String id) {
      for (var f : fields)
        if (f.id.equals(id))
          return f;
      return null;
    }
    private List<String> eligible() {
      var ids = new ArrayList<String>();
      for (var f : fields)
        if (f.state.focusable())
          ids.add(f.id);
      if (!ids.contains(focused))
        focused = ids.isEmpty() ? "" : ids.get(0);
      return ids;
    }
    public List<Field> fields() {
      return Collections.unmodifiableList(fields);
    }
    public String value(String id) {
      var t = inputs.get(id);
      if (t != null)
        return t.value();
      var f = field(id);
      if (f == null)
        throw new IllegalArgumentException("unknown field");
      return f.value;
    }
    public boolean focus(String id) {
      var f = field(id);
      if (f == null || !f.state.focusable())
        return false;
      for (var v : fields) v.open = false;
      focused = id;
      return true;
    }
    public boolean atTabBoundary(boolean previous) {
      var ids = eligible();
      return ids.isEmpty() || focused.equals(ids.get(previous ? 0 : ids.size() - 1));
    }
    public boolean setState(String id, State state) {
      var f = field(id);
      if (f == null)
        return false;
      f.state = copyState(state);
      if (!state.editable())
        f.open = false;
      eligible();
      return true;
    }
    public boolean setFeedback(String id, String help, String error) {
      var f = field(id);
      if (f == null)
        return false;
      f.help = help;
      f.error = error;
      f.state.invalid = !error.isEmpty();
      return true;
    }
    public boolean selectText(String id, int a, int c) {
      var t = inputs.get(id);
      if (t == null)
        return false;
      t.select(a, c);
      return true;
    }
    public List<String> missing() {
      var out = new ArrayList<String>();
      for (var f : fields) {
        boolean empty = false;
        if (inputs.containsKey(f.id))
          empty = value(f.id).codePoints().allMatch(cp
              -> (cp >= 9 && cp <= 13) || cp == 32 || cp == 0x85 || cp == 0xa0 || cp == 0x1680
                  || (cp >= 0x2000 && cp <= 0x200a) || cp == 0x2028 || cp == 0x2029 || cp == 0x202f
                  || cp == 0x205f || cp == 0x3000);
        else if (f.kind.equals("checkbox"))
          empty = !f.checked;
        else if (f.kind.equals("radio") || f.kind.equals("select"))
          empty = f.choice.isEmpty();
        if (!f.state.disabled && (f.state.invalid || !f.error.isEmpty() || f.required && empty))
          out.add(f.id);
      }
      return out;
    }
    public FormEvent handle(String action) {
      return handle(action, "");
    }
    public FormEvent handle(String action, String text) {
      var ids = eligible();
      if (action.equals("next") || action.equals("previous")) {
        if (!ids.isEmpty()) {
          int at = ids.indexOf(focused);
          focus(ids.get((at + ids.size() + (action.equals("next") ? 1 : -1)) % ids.size()));
        }
        return new FormEvent();
      }
      if (action.equals("submit")) {
        var missing = missing();
        return new FormEvent(
            missing.isEmpty() ? "submit" : "invalid", "", "", List.copyOf(missing));
      }
      var f = field(focused);
      if (f == null)
        return new FormEvent();
      if (action.equals("cancel")) {
        if (f.open) {
          f.open = false;
          return new FormEvent();
        }
        return new FormEvent("cancel", f.id);
      }
      if (action.equals("insert") && text.equals(" ") && !inputs.containsKey(f.id))
        action = "toggle";
      var input = inputs.get(f.id);
      if (input != null) {
        input.state = copyState(f.state);
        if (action.equals("activate") && !f.kind.equals("textarea"))
          return f.state.activatable() ? handle("submit") : new FormEvent();
        var e = input.handle(action.equals("activate") ? "newline" : action, text);
        f.value = input.display();
        f.state = copyState(input.state);
        return new FormEvent(e.kind(), f.id, e.text(), List.of());
      }
      if (f.kind.equals("button") && List.of("left", "right").contains(action)
          && !f.state.disabled) {
        handle(action.equals("left") ? "previous" : "next");
        return new FormEvent();
      }
      if (!f.state.activatable())
        return new FormEvent();
      if (f.kind.equals("button") && List.of("activate", "toggle").contains(action))
        return f.action.equals("submit")
            ? handle("submit")
            : new FormEvent(f.action.equals("cancel") ? "cancel" : "activate", f.id);
      if (!f.state.editable())
        return new FormEvent();
      boolean changed = false;
      if (f.kind.equals("checkbox") && List.of("activate", "toggle").contains(action)) {
        f.checked = !f.checked;
        changed = true;
      } else if (f.kind.equals("radio") || f.kind.equals("select")) {
        if (f.kind.equals("select") && List.of("activate", "toggle").contains(action)) {
          if (f.open) {
            f.choice = f.pending;
            f.open = false;
            changed = true;
          } else {
            f.open = true;
            f.pending = f.choice;
            if (f.pending.isEmpty())
              for (var o : f.options)
                if (!o.disabled()) {
                  f.pending = o.id();
                  break;
                }
            return new FormEvent();
          }
        } else if (List.of("left", "right", "up", "down", "activate", "toggle").contains(action)) {
          if (f.kind.equals("select") && !f.open)
            return new FormEvent();
          var choices = new ArrayList<String>();
          for (var o : f.options)
            if (!o.disabled())
              choices.add(o.id());
          if (choices.isEmpty())
            return new FormEvent();
          int at = choices.indexOf(f.open ? f.pending : f.choice),
              target = List.of("left", "up").contains(action)
              ? (Math.max(0, at) + choices.size() - 1) % choices.size()
              : at < 0 ? 0
                       : (at + 1) % choices.size();
          if (f.kind.equals("select"))
            f.pending = choices.get(target);
          else {
            f.choice = choices.get(target);
            changed = true;
          }
        }
      }
      if (changed) {
        f.state.edited = true;
        return new FormEvent("change", f.id);
      }
      return new FormEvent();
    }
    public FormEvent clickField(String id, String option) {
      var f = field(id);
      if (f == null || f.state.disabled)
        return new FormEvent();
      for (var o : f.options)
        if (o.id().equals(option) && o.disabled())
          return new FormEvent();
      if (!focused.equals(id))
        focus(id);
      if (f.kind.equals("button"))
        return handle("activate");
      if (!f.state.editable())
        return new FormEvent();
      if (f.kind.equals("select") && !f.open)
        return handle("activate");
      if (!option.isEmpty() && List.of("radio", "select").contains(f.kind)) {
        for (var o : f.options)
          if (o.id().equals(option) && !o.disabled()) {
            f.choice = option;
            f.open = false;
            f.state.edited = true;
            return new FormEvent("change", f.id);
          }
        return new FormEvent();
      }
      return List.of("checkbox", "select").contains(f.kind) ? handle("activate") : new FormEvent();
    }
    public List<FormRow> layout(int width, int height) {
      var rows = new ArrayList<FormRow>();
      int anchor = 0;
      for (var f : fields) {
        boolean current = f.id.equals(focused);
        if (current)
          anchor = rows.size();
        String role = f.state.disabled              ? "disabled"
            : !f.error.isEmpty() || f.state.invalid ? "error"
                                                    : f.state.role(),
               markers = f.state.markers();
        if (f.state.disabled)
          markers = markers.replaceFirst("^-", "");
        rows.add(new FormRow(f.id,
            (current ? "> " : "  ") + f.label + (f.required ? " *" : "")
                + (markers.isEmpty() ? "" : " " + markers),
            role, "", false, current, 0));
        if (inputs.containsKey(f.id)) {
          String display = inputs.get(f.id).display();
          String[] lines = f.kind.equals("textarea") ? display.split("\\r\\n|\\r|\\n", -1)
                                                     : new String[] {display};
          int count = f.kind.equals("textarea") ? Math.max(1, f.height) : 1;
          for (int i = 0; i < Math.min(count, lines.length); i++)
            rows.add(new FormRow(f.id, "  " + lines[i], f.state.disabled ? "disabled" : "field", "",
                true, false, i));
        } else if (f.kind.equals("checkbox"))
          rows.add(new FormRow(f.id, f.checked ? "  [x]" : "  [ ]", role, "", false, false, 0));
        else if (f.kind.equals("button"))
          rows.add(new FormRow(f.id, "  [ " + f.label + (f.state.busy ? " ~" : "") + " ]",
              f.state.disabled   ? "disabled"
                  : f.state.busy ? "hint"
                                 : "button",
              "", false, current, 0));
        else
          for (var o : f.options) {
            if (f.kind.equals("select") && !f.open && !o.id().equals(f.choice))
              continue;
            rows.add(new FormRow(f.id,
                "  (" + (o.id().equals(f.open ? f.pending : f.choice) ? "*" : " ") + ") "
                    + o.label(),
                o.disabled() || f.state.disabled ? "disabled" : role, o.id(), false, false, 0));
          }
        if (!f.error.isEmpty())
          rows.add(new FormRow(f.id, "! " + f.error, "error", "", false, false, 0));
        else if (!f.help.isEmpty())
          rows.add(new FormRow(f.id, "  " + f.help, "hint", "", false, false, 0));
      }
      width = Math.max(0, width);
      height = Math.max(0, height);
      scroll = Math.min(
          Math.max(0, anchor - Math.max(0, height - 2)), Math.max(0, rows.size() - height));
      var visible = new ArrayList<FormRow>();
      for (var row : rows.subList(scroll, Math.min(rows.size(), scroll + height)))
        visible.add(new FormRow(row.id(), clip(row.text(), width, false), row.role(), row.option(),
            row.input(), row.focused(), row.sourceRow()));
      layoutWidth = width;
      hits = visible;
      return List.copyOf(visible);
    }
    public FormEvent click(int x, int y, int height) {
      if (x < 0 || x >= layoutWidth || y < 0 || y >= height || y >= hits.size())
        return new FormEvent();
      var row = hits.get(y);
      if (row.input() && x >= 2) {
        var f = field(row.id());
        if (f == null || f.state.disabled)
          return new FormEvent();
        if (!focused.equals(f.id))
          focus(f.id);
        int first = -1, count = 0;
        for (int i = 0; i < hits.size(); i++)
          if (hits.get(i).id().equals(f.id) && hits.get(i).input()) {
            if (first < 0)
              first = i;
            count++;
          }
        var e =
            inputs.get(f.id).click(x - 2, y - first, Math.max(0, layoutWidth - 2), count, false);
        return new FormEvent(e.kind(), f.id, e.text(), List.of());
      }
      return clickField(row.id(), row.option());
    }
    public void draw(Canvas c, Rect r, boolean focusedView) {
      c.fill(r, "surface");
      var rows = layout(r.width(), r.height());
      for (int y = 0; y < rows.size(); y++) {
        var row = rows.get(y);
        c.write(r.x(), r.y() + y, row.text(), row.role(), focusedView && row.focused(), r.width());
      }
      for (var f : fields) {
        int first = -1, count = 0;
        for (int i = 0; i < rows.size(); i++)
          if (rows.get(i).id().equals(f.id) && rows.get(i).input()) {
            if (first < 0)
              first = i;
            count++;
          }
        if (first >= 0) {
          var t = inputs.get(f.id);
          t.state = copyState(f.state);
          t.draw(c,
              new Rect(
                  r.x() + Math.min(2, r.width()), r.y() + first, Math.max(0, r.width() - 2), count),
              focusedView && focused.equals(f.id));
        }
      }
    }
  }
  public static final class Control extends Form {
    public Control(Field field) {
      super(List.of(field));
    }
  }
  public record FocusTarget(String id, State state, boolean hidden) {
    public FocusTarget(String id) {
      this(id, new State(), false);
    }
  }
  public record InputRoute(String scopeId, boolean blocked) {}
  public record PopupCloseRequest(String id, String reason) {}
  public static final class Focus {
    private static final class Scope {
      String id, focused = "", restore = "";
      List<FocusTarget> targets;
      boolean dismissible;
      Scope(String id, List<FocusTarget> targets, boolean dismissible) {
        this.id = id;
        this.targets = owned(targets);
        this.dismissible = dismissible;
        reconcile(this);
      }
    }
    private final List<Scope> scopes = new ArrayList<>();
    private static List<FocusTarget> owned(List<FocusTarget> targets) {
      var ids = new HashSet<String>();
      var out = new ArrayList<FocusTarget>();
      for (var t : targets) {
        if (t.id().isEmpty() || !ids.add(t.id()))
          throw new IllegalArgumentException("invalid target ID");
        out.add(new FocusTarget(t.id(), copyState(t.state()), t.hidden()));
      }
      return out;
    }
    private static List<String> ids(Scope s) {
      var out = new ArrayList<String>();
      for (var t : s.targets)
        if (!t.hidden() && t.state().focusable())
          out.add(t.id());
      return out;
    }
    private static void reconcile(Scope s) {
      var ids = ids(s);
      if (!ids.contains(s.focused))
        s.focused = ids.isEmpty() ? "" : ids.get(0);
    }
    public Focus(String id, List<FocusTarget> targets) {
      if (id.isEmpty())
        throw new IllegalArgumentException("empty root scope");
      scopes.add(new Scope(id, targets, false));
    }
    private Scope top() {
      return scopes.get(scopes.size() - 1);
    }
    public String focused() {
      return top().focused;
    }
    public String scopeId() {
      return top().id;
    }
    public int depth() {
      return scopes.size() - 1;
    }
    public boolean focus(String id) {
      if (!ids(top()).contains(id))
        return false;
      top().focused = id;
      return true;
    }
    public String move(boolean previous) {
      var s = top();
      var ids = ids(s);
      if (ids.isEmpty())
        s.focused = "";
      else {
        int at = ids.indexOf(s.focused),
            next = previous ? (Math.max(0, at) + ids.size() - 1) % ids.size()
            : at < 0        ? 0
                            : (at + 1) % ids.size();
        s.focused = ids.get(next);
      }
      return s.focused;
    }
    public void open(String id, List<FocusTarget> targets, String initial, boolean dismissible) {
      if (id.isEmpty() || scopes.size() >= 65 || scopes.stream().anyMatch(s -> s.id.equals(id)))
        throw new IllegalArgumentException("invalid scope or depth");
      var s = new Scope(id, targets, dismissible);
      s.restore = focused();
      if (!initial.isEmpty()) {
        if (!ids(s).contains(initial))
          throw new IllegalArgumentException("initial target not focusable");
        s.focused = initial;
      }
      scopes.add(s);
    }
    public void open(String id, List<FocusTarget> targets) {
      open(id, targets, "", true);
    }
    public void update(String id, List<FocusTarget> targets) {
      var next = owned(targets);
      for (var s : scopes)
        if (s.id.equals(id)) {
          s.targets = next;
          reconcile(s);
          return;
        }
      throw new IllegalArgumentException("unknown scope");
    }
    public Event close(String id) {
      if (depth() == 0 || !scopeId().equals(id))
        throw new IllegalArgumentException("only top popup can close");
      String restore = top().restore;
      scopes.remove(scopes.size() - 1);
      if (!focus(restore))
        reconcile(top());
      return new Event("focus", focused());
    }
    public Optional<PopupCloseRequest> requestClose() {
      return depth() > 0 && top().dismissible
          ? Optional.of(new PopupCloseRequest(scopeId(), "escape"))
          : Optional.empty();
    }
    public InputRoute route(String target) {
      return new InputRoute(scopeId(), !target.isEmpty() && !target.equals(scopeId()));
    }
    public boolean blocked(String target) {
      return route(target).blocked();
    }
  }
  public static String fold(String text) {
    var out = new StringBuilder();
    text.codePoints().forEach(cp -> {
      int index = Arrays.binarySearch(FoldData.KEYS, cp);
      if (index >= 0)
        out.append(FoldData.VALUES[index]);
      else
        out.appendCodePoint(cp);
    });
    return out.toString();
  }
  public static final class Item {
    public String id, label = "", secondary = "", shortcut = "", icon = "", asciiIcon = "",
                      parent = "";
    public boolean disabled, separator;
    public Item(String id) {
      this.id = id;
    }
    public Item(String id, String label) {
      this.id = id;
      this.label = label;
    }
  }
  public record CollectionRow(String id, String text, String role, boolean focused) {}
  public static final class ListModel {
    private List<Item> items = List.of();
    private List<CollectionRow> hits = List.of();
    private int layoutWidth;
    public String focused = "", selected = "", query = "", empty = "(empty)";
    public int scroll;
    public ListModel(List<Item> items) {
      setItems(items);
    }
    public List<Item> items() {
      return Collections.unmodifiableList(items);
    }
    public void setItems(List<Item> source) {
      var ids = new HashSet<String>();
      var owned = new ArrayList<Item>();
      for (var i : source) {
        if (i.id.isEmpty() || !ids.add(i.id))
          throw new IllegalArgumentException("invalid list ID");
        var v = new Item(i.id, i.label);
        v.secondary = i.secondary;
        v.shortcut = i.shortcut;
        v.icon = i.icon;
        v.asciiIcon = i.asciiIcon;
        v.parent = i.parent;
        v.disabled = i.disabled;
        v.separator = i.separator;
        owned.add(v);
      }
      if (owned.stream().noneMatch(i -> i.id.equals(selected)))
        selected = "";
      items = owned;
      eligible();
    }
    public List<Item> visible() {
      String q = fold(query);
      var out = new ArrayList<Item>();
      for (var i : items)
        if (q.isEmpty() || !i.separator && fold(i.label + " " + i.secondary).contains(q))
          out.add(i);
      return out;
    }
    private List<String> eligible() {
      var ids = new ArrayList<String>();
      for (var i : visible())
        if (!i.disabled && !i.separator)
          ids.add(i.id);
      if (!ids.contains(focused))
        focused = ids.isEmpty() ? "" : ids.get(0);
      return ids;
    }
    public boolean focus(String id) {
      for (var i : visible())
        if (i.id.equals(id) && !i.disabled && !i.separator) {
          focused = id;
          return true;
        }
      return false;
    }
    public Event setQuery(String text) {
      query = text.replaceAll("[\\x00-\\x1f\\x7f-\\x9f]", "");
      eligible();
      return new Event("query", "", query);
    }
    public Event handle(String action, int height) {
      return handle(action, height, "");
    }
    public Event handle(String action, int height, String text) {
      if (action.equals("query"))
        return setQuery(text);
      var ids = eligible();
      if (ids.isEmpty())
        return new Event();
      int at = ids.indexOf(focused);
      if (action.equals("activate") || action.equals("select")) {
        selected = focused;
        return new Event(action, focused);
      }
      action = switch (action) {
        case "up" -> "previous";
        case "down" -> "next";
        case "home" -> "first";
        case "end" -> "last";
        default -> action;
      };
      switch (action) {
        case "previous" -> at = Math.max(0, at - 1);
        case "next" -> at = Math.min(ids.size() - 1, at + 1);
        case "first" -> at = 0;
        case "last" -> at = ids.size() - 1;
        case "page_up" -> at = Math.max(0, at - (height > 1 ? height - 1 : 1));
        case "page_down" -> at = Math.min(ids.size() - 1, at + (height > 1 ? height - 1 : 1));
        default -> {
          return new Event();
        }
      }
      focused = ids.get(at);
      return new Event("focus", focused);
    }
    public List<CollectionRow> layout(int width, int height, boolean ascii) {
      var rows = new ArrayList<CollectionRow>();
      int anchor = 0;
      for (var i : visible()) {
        boolean current = i.id.equals(focused);
        if (current)
          anchor = rows.size();
        String role = i.disabled ? "disabled" : i.id.equals(selected) ? "selection" : "body";
        if (i.separator) {
          rows.add(new CollectionRow(i.id, "--- " + i.label + " ---", "hint", false));
          continue;
        }
        String icon = ascii ? i.asciiIcon : i.icon;
        rows.add(new CollectionRow(i.id,
            (current ? "> " : "  ") + (i.id.equals(selected) ? "* " : "")
                + (icon.isEmpty() ? "" : icon + " ") + i.label
                + (i.shortcut.isEmpty() ? "" : " [" + i.shortcut + "]"),
            role, current));
        if (!i.secondary.isEmpty())
          rows.add(new CollectionRow(
              i.id, "    " + i.secondary, i.disabled ? "disabled" : "hint", false));
      }
      if (rows.isEmpty())
        rows.add(new CollectionRow("", empty, "hint", false));
      width = Math.max(0, width);
      height = Math.max(0, height);
      scroll = Math.min(
          Math.max(0, anchor - Math.max(0, height - 2)), Math.max(0, rows.size() - height));
      layoutWidth = width;
      var out = new ArrayList<CollectionRow>();
      for (var row : rows.subList(scroll, Math.min(rows.size(), scroll + height)))
        out.add(
            new CollectionRow(row.id(), clip(row.text(), width, true), row.role(), row.focused()));
      hits = out;
      return List.copyOf(out);
    }
    public Event clickId(String id) {
      return focus(id) ? handle("activate", 10) : new Event();
    }
    public Event click(int x, int y, int height) {
      return x >= 0 && x < layoutWidth && y >= 0 && y < height && y < hits.size()
          ? clickId(hits.get(y).id())
          : new Event();
    }
    public void draw(Canvas c, Rect r, boolean focusedView, boolean ascii) {
      c.fill(r, "surface");
      var rows = layout(r.width(), r.height(), ascii);
      for (int y = 0; y < rows.size(); y++) {
        var row = rows.get(y);
        c.fill(new Rect(r.x(), r.y() + y, r.width(), 1), row.role());
        c.write(r.x(), r.y() + y, row.text(), row.role(), focusedView && row.focused(), r.width());
      }
    }
  }
  public static final class SearchPicker {
    public final ListModel list;
    public boolean open;
    public String value = "";
    private int width, height;
    public SearchPicker(List<Item> items) {
      list = new ListModel(items);
    }
    public Event handle(String action) {
      return handle(action, "", 10);
    }
    public Event handle(String action, String text, int viewHeight) {
      if (action.equals("open")) {
        open = true;
        list.setQuery("");
        list.focus(value);
        return new Event("open", "");
      }
      if (action.equals("cancel")) {
        open = false;
        return new Event("cancel", "");
      }
      if (action.equals("insert") || action.equals("backspace")) {
        if (!open)
          handle("open");
        String query = list.query;
        if (action.equals("insert"))
          query += text;
        else {
          var g = graphemes(query);
          if (!g.isEmpty())
            g.remove(g.size() - 1);
          query = String.join("", g);
        }
        return list.setQuery(query);
      }
      if (action.equals("activate")) {
        if (!open)
          return handle("open");
        var e = list.handle("activate", viewHeight);
        if (!e.id().isEmpty()) {
          value = e.id();
          open = false;
          return new Event("change", e.id());
        }
        return e;
      }
      return open ? list.handle(action, viewHeight) : new Event();
    }
    public Event clickId(String id) {
      return list.focus(id) ? handle("activate") : new Event();
    }
    public Event click(int x, int y, int viewHeight) {
      if (x < 0 || x >= width || y < 0 || y >= Math.min(height, viewHeight))
        return new Event();
      if (!open)
        return handle("open");
      if (y == 0)
        return new Event();
      var e = list.click(x, y - 1, Math.max(0, viewHeight - 1));
      if (!e.id().isEmpty()) {
        value = e.id();
        open = false;
        return new Event("change", e.id());
      }
      return new Event();
    }
    public List<CollectionRow> layout(int width, int height, boolean ascii) {
      this.width = Math.max(0, width);
      this.height = Math.max(0, height);
      width = this.width;
      height = this.height;
      if (height <= 0)
        return List.of();
      if (!open) {
        String label = list.empty;
        for (var i : list.items())
          if (i.id.equals(value))
            label = i.label;
        return List.of(new CollectionRow(value, clip("v " + label, width, false), "field", false));
      }
      String query = "";
      int used = 0;
      var gs = graphemes(list.query);
      for (int i = gs.size() - 1; i >= 0; i--) {
        int n = cells(gs.get(i));
        if (used + n > Math.max(0, width - 3))
          break;
        query = gs.get(i) + query;
        used += n;
      }
      var rows = new ArrayList<CollectionRow>();
      rows.add(new CollectionRow("", clip("? " + query, width, false), "field", false));
      rows.addAll(list.layout(width, Math.max(0, height - 1), ascii));
      return rows;
    }
    public void draw(Canvas c, Rect r, boolean focused, boolean ascii) {
      c.fill(r, "surface");
      var rows = layout(r.width(), r.height(), ascii);
      if (!open) {
        if (!rows.isEmpty()) {
          c.fill(new Rect(r.x(), r.y(), r.width(), 1), "field");
          c.write(r.x(), r.y(), rows.get(0).text(), "field");
        }
        return;
      }
      if (r.height() > 0) {
        c.fill(new Rect(r.x(), r.y(), r.width(), 1), "field");
        c.write(r.x(), r.y(), "? ", "field");
        if (r.width() > 2) {
          var query = new Text(list.query);
          query.multiline = false;
          query.draw(c, new Rect(r.x() + 2, r.y(), r.width() - 2, 1), focused);
        }
      }
      if (r.height() > 1)
        list.draw(c, new Rect(r.x(), r.y() + 1, r.width(), r.height() - 1), focused, ascii);
    }
  }
  public static final class MenuItem {
    public String id, parent = "", label = "", secondary = "", shortcut = "", mnemonic = "",
                      icon = "", asciiIcon = "";
    public boolean disabled, separator;
    public MenuItem(String id) {
      this.id = id;
    }
    public MenuItem(String id, String label) {
      this.id = id;
      this.label = label;
    }
  }
  public record MenuEvent(String kind, String id, String returnId) {
    public MenuEvent() {
      this("", "", "");
    }
  }
  public record MenuSpan(int start, int width, String text, String role) {}
  public record
      MenuRow(String id, String text, String role, List<MenuSpan> spans, boolean focused) {}
  public record
      MenuBarCell(String id, String text, String role, int start, int width, boolean focused) {}
  public record MenuBarLayout(List<MenuBarCell> cells, boolean previous, boolean next) {}
  public static final class Menu {
    private List<MenuItem> items = List.of();
    private Map<String, MenuItem> index = new LinkedHashMap<>();
    private Map<String, List<String>> children = new LinkedHashMap<>();
    private final List<String> path = new ArrayList<>();
    private final Map<String, String> focusMap = new HashMap<>();
    private final Map<String, Integer> tops = new HashMap<>();
    private List<MenuRow> hits = List.of();
    private boolean opened, context;
    private String caller = "", bar = "";
    private int barFirst, width;
    public String backLabel = "Back", emptyLabel = "(empty)";
    public Menu(List<MenuItem> items) {
      setItems(items);
    }
    private static MenuItem copy(MenuItem i) {
      var v = new MenuItem(i.id, i.label);
      v.parent = i.parent;
      v.secondary = i.secondary;
      v.shortcut = i.shortcut;
      v.mnemonic = i.mnemonic;
      v.icon = i.icon;
      v.asciiIcon = i.asciiIcon;
      v.disabled = i.disabled;
      v.separator = i.separator;
      return v;
    }
    private static boolean mnemonic(String s) {
      return s.matches("[A-Za-z0-9]");
    }
    private static void validate(List<MenuItem> items) {
      if (items.size() > 10000)
        throw new IllegalArgumentException("too many menu items");
      var index = new HashMap<String, MenuItem>();
      var keys = new HashMap<String, Set<String>>();
      var parents = new HashSet<String>();
      for (var i : items) {
        if (i.id.isEmpty() || i.id.startsWith("@") || index.putIfAbsent(i.id, i) != null)
          throw new IllegalArgumentException("invalid menu ID");
        parents.add(i.parent);
        if (!i.mnemonic.isEmpty()) {
          String key = i.mnemonic.toLowerCase(Locale.ROOT);
          if (!mnemonic(i.mnemonic) || i.separator
              || !keys.computeIfAbsent(i.parent, p -> new HashSet<>()).add(key))
            throw new IllegalArgumentException("invalid sibling mnemonic");
        }
      }
      for (var i : items) {
        if (i.separator && parents.contains(i.id))
          throw new IllegalArgumentException("separator children");
        var seen = new HashSet<String>();
        seen.add(i.id);
        String parent = i.parent;
        int depth = 1;
        while (!parent.isEmpty()) {
          var p = index.get(parent);
          if (p == null || !seen.add(parent) || p.separator)
            throw new IllegalArgumentException("invalid parent/cycle");
          if (++depth > 32)
            throw new IllegalArgumentException("menu depth exceeds32");
          parent = p.parent;
        }
      }
    }
    public MenuEvent setItems(List<MenuItem> source) {
      var owned = new ArrayList<MenuItem>();
      for (var i : source) owned.add(copy(i));
      validate(owned);
      var idx = new LinkedHashMap<String, MenuItem>();
      var ch = new LinkedHashMap<String, List<String>>();
      for (var i : owned) {
        idx.put(i.id, i);
        ch.computeIfAbsent(i.parent, p -> new ArrayList<>()).add(i.id);
      }
      items = owned;
      index = idx;
      children = ch;
      focusMap.keySet().removeIf(p -> !p.isEmpty() && !index.containsKey(p));
      tops.keySet().removeIf(p -> !p.isEmpty() && !index.containsKey(p));
      hits = List.of();
      if (!usable(bar, ""))
        bar = first("");
      for (int n = 0; n < path.size(); n++)
        if (!usable(path.get(n), n > 0 ? path.get(n - 1) : "") || childIds(path.get(n)).isEmpty())
          return close();
      if (opened)
        reconcile();
      return new MenuEvent();
    }
    public List<MenuItem> items() {
      var out = new ArrayList<MenuItem>();
      for (var i : items) out.add(copy(i));
      return out;
    }
    public boolean opened() {
      return opened;
    }
    public List<String> path() {
      return List.copyOf(path);
    }
    public String focusedId() {
      return focusMap.getOrDefault(parent(), "");
    }
    public String returnId() {
      return caller;
    }
    public String barFocusedId() {
      return bar;
    }
    private List<String> childIds(String p) {
      return children.getOrDefault(p, List.of());
    }
    private String parent() {
      return path.isEmpty() ? "" : path.get(path.size() - 1);
    }
    private boolean usable(String id, String p) {
      var i = index.get(id);
      return i != null && i.parent.equals(p) && !i.disabled && !i.separator;
    }
    private String first(String p) {
      for (var id : childIds(p))
        if (usable(id, p))
          return id;
      return "";
    }
    private boolean backAllowed() {
      return path.size() > 1 || context && !path.isEmpty();
    }
    private void reconcile() {
      String p = parent(), id = focusedId();
      if (id.equals("@back") && backAllowed())
        return;
      if (!usable(id, p)) {
        String first = first(p);
        focusMap.put(p, first.isEmpty() && backAllowed() ? "@back" : first);
      }
    }
    public String title() {
      var labels = new ArrayList<String>();
      for (String id : path) labels.add(clean(index.get(id).label));
      return String.join(" / ", labels);
    }
    private MenuEvent event(String kind, String id) {
      return new MenuEvent(kind, id, caller);
    }
    private MenuEvent finish(String kind, String id) {
      opened = false;
      path.clear();
      hits = List.of();
      return event(kind, id);
    }
    public MenuEvent open(String id, String returnId) {
      var next = new ArrayList<String>();
      String at = id;
      while (!at.isEmpty()) {
        var i = index.get(at);
        if (i == null || i.disabled || i.separator)
          return new MenuEvent();
        next.add(0, at);
        at = i.parent;
      }
      caller = returnId;
      path.clear();
      path.addAll(next);
      hits = List.of();
      for (int n = 0; n < path.size(); n++) focusMap.put(n > 0 ? path.get(n - 1) : "", path.get(n));
      context = id.isEmpty();
      opened = true;
      if (!path.isEmpty())
        bar = path.get(0);
      if (!id.isEmpty() && childIds(id).isEmpty())
        return finish("activate", id);
      reconcile();
      return event("open", id);
    }
    public MenuEvent close() {
      return opened ? finish("close", "") : new MenuEvent();
    }
    public MenuEvent back() {
      if (!opened)
        return new MenuEvent();
      if (!backAllowed())
        return close();
      path.remove(path.size() - 1);
      reconcile();
      return event("back", parent());
    }
    public boolean focus(String id) {
      if (!opened)
        return false;
      if (id.equals("@back") && backAllowed() || usable(id, parent())) {
        focusMap.put(parent(), id);
        return true;
      }
      return false;
    }
    private MenuEvent enter(String id) {
      path.add(id);
      reconcile();
      return event("open", id);
    }
    private MenuEvent switchRoot(boolean next) {
      var ids = new ArrayList<String>();
      for (String id : childIds(""))
        if (usable(id, ""))
          ids.add(id);
      if (ids.isEmpty())
        return new MenuEvent();
      int at = Math.max(0, ids.indexOf(bar)), step = next ? 1 : ids.size() - 1;
      for (int n = 0; n < ids.size(); n++) {
        at = (at + step) % ids.size();
        if (!ids.get(at).equals(bar) && !childIds(ids.get(at)).isEmpty())
          return open(ids.get(at), caller);
      }
      return new MenuEvent();
    }
    public MenuEvent handle(String action) {
      return handle(action, "", 10);
    }
    public MenuEvent handle(String action, String value, int height) {
      if (!opened)
        return new MenuEvent();
      reconcile();
      String p = parent(), id = focusedId();
      if (action.equals("cancel") || action.equals("back"))
        return back();
      if (action.equals("close"))
        return close();
      if (action.equals("left"))
        return backAllowed() ? back() : context ? new MenuEvent() : switchRoot(false);
      if (action.equals("right")) {
        if (usable(id, p) && !childIds(id).isEmpty())
          return enter(id);
        return !backAllowed() && !context ? switchRoot(true) : new MenuEvent();
      }
      if (action.equals("activate")) {
        if (id.equals("@back"))
          return back();
        if (!usable(id, p))
          return new MenuEvent();
        return childIds(id).isEmpty() ? finish("activate", id) : enter(id);
      }
      if (action.equals("mnemonic")) {
        if (!mnemonic(value))
          return new MenuEvent();
        for (String candidate : childIds(p)) {
          var i = index.get(candidate);
          if (usable(candidate, p) && !i.mnemonic.isEmpty() && i.mnemonic.equalsIgnoreCase(value)) {
            focusMap.put(p, candidate);
            return handle("activate", "", height);
          }
        }
        return new MenuEvent();
      }
      var ids = new ArrayList<String>();
      if (backAllowed())
        ids.add("@back");
      for (String candidate : childIds(p))
        if (usable(candidate, p))
          ids.add(candidate);
      if (ids.isEmpty())
        return new MenuEvent();
      int at = Math.max(0, ids.indexOf(id)), step = height > 1 ? height - 1 : 1;
      switch (action) {
        case "previous", "up" -> at = (at + ids.size() - 1) % ids.size();
        case "next", "down" -> at = (at + 1) % ids.size();
        case "first", "home" -> at = 0;
        case "last", "end" -> at = ids.size() - 1;
        case "page_up" -> at = Math.max(0, at - step);
        case "page_down" -> at = (int) Math.min(ids.size() - 1, (long) at + step);
        default -> {
          return new MenuEvent();
        }
      }
      focusMap.put(p, ids.get(at));
      return event("focus", ids.get(at));
    }
    public MenuEvent handleBar(String action, String value) {
      var ids = new ArrayList<String>();
      for (String id : childIds(""))
        if (usable(id, ""))
          ids.add(id);
      if (ids.isEmpty())
        return new MenuEvent();
      int at = Math.max(0, ids.indexOf(bar));
      switch (action) {
        case "previous", "left" -> at = (at + ids.size() - 1) % ids.size();
        case "next", "right" -> at = (at + 1) % ids.size();
        case "first", "home" -> at = 0;
        case "last", "end" -> at = ids.size() - 1;
        case "activate", "down" -> {
          return new MenuEvent("open_request", ids.get(at), "");
        }
        case "mnemonic" -> {
          if (!mnemonic(value))
            return new MenuEvent();
          for (String id : ids) {
            var i = index.get(id);
            if (!i.mnemonic.isEmpty() && i.mnemonic.equalsIgnoreCase(value)) {
              bar = id;
              return new MenuEvent("open_request", id, "");
            }
          }
          return new MenuEvent();
        }
        default -> {
          return new MenuEvent();
        }
      }
      bar = ids.get(at);
      return new MenuEvent("focus", bar, "");
    }
    public MenuEvent clickId(String id) {
      return focus(id) ? handle("activate") : new MenuEvent();
    }
    public MenuEvent click(int x, int y, int height) {
      return opened && x >= 0 && x < width && y >= 0 && y < height && y < hits.size()
          ? clickId(hits.get(y).id())
          : new MenuEvent();
    }
    private static String label(MenuItem i) {
      return i.label
          + (i.mnemonic.isEmpty() ? "" : " (" + i.mnemonic.toUpperCase(Locale.ROOT) + ")");
    }
    private List<MenuItem> rows() {
      var out = new ArrayList<MenuItem>();
      if (backAllowed()) {
        out.add(new MenuItem("@back", backLabel));
        var separator = new MenuItem("");
        separator.separator = true;
        out.add(separator);
      }
      for (String id : childIds(parent())) out.add(index.get(id));
      return out;
    }
    public int[] contentSize() {
      var rows = rows();
      int width = 12;
      for (var i : rows)
        width = Math.max(
            width, cells(label(i)) + cells(i.secondary) + cells(i.shortcut) + cells(i.icon) + 8);
      return new int[] {Math.min(4096, width), Math.max(1, rows.size())};
    }
    public List<MenuRow> layout(int width, int height, boolean ascii) {
      hits = List.of();
      this.width = width = Math.max(0, Math.min(65535, width));
      height = Math.max(0, Math.min(4096, height));
      if (!opened || width == 0 || height == 0)
        return List.of();
      reconcile();
      var rows = rows();
      if (rows.isEmpty()) {
        hits = List.of(new MenuRow("", clip(emptyLabel, width, true), "hint", List.of(), false));
        return hits;
      }
      int at = 0;
      for (int n = 0; n < rows.size(); n++)
        if (rows.get(n).id.equals(focusedId()))
          at = n;
      String p = parent();
      int top = Math.min(tops.getOrDefault(p, 0), at);
      if (at >= top + height)
        top = at - height + 1;
      top = Math.min(top, Math.max(0, rows.size() - height));
      tops.put(p, top);
      var out = new ArrayList<MenuRow>();
      for (var i : rows.subList(top, Math.min(rows.size(), top + height))) {
        if (i.separator) {
          out.add(new MenuRow("", (ascii ? "-" : "─").repeat(width), "hint", List.of(), false));
          continue;
        }
        boolean current = i.id.equals(focusedId());
        String role = i.disabled ? "disabled"
            : current            ? "selection"
                                 : "surface",
               icon = ascii ? (i.asciiIcon.isEmpty() && !i.icon.isEmpty() ? "*" : i.asciiIcon)
                            : i.icon,
               text = (current ? "> " : "  ") + (icon.isEmpty() ? "" : icon + " ")
            + (i.id.equals("@back") ? "< " + i.label : label(i))
            + (i.secondary.isEmpty() ? "" : "  " + i.secondary),
               suffix = childIds(i.id).isEmpty() ? ""
            : ascii                              ? " >"
                                                 : " ›",
               shortcut = clean(i.shortcut);
        int reserve = Math.min(width / 3, cells(shortcut));
        String tail = reserve > 0 ? " " + clip(shortcut, reserve, false) + suffix : suffix;
        int tw = Math.min(width, cells(tail));
        String left = clip(text, width - tw, true);
        var spans = new ArrayList<MenuSpan>();
        spans.add(new MenuSpan(0, width, left, role));
        if (tw > 0)
          spans.add(new MenuSpan(
              width - tw, tw, clip(tail, tw, false), role.equals("surface") ? "hint" : role));
        out.add(new MenuRow(i.id,
            left + " ".repeat(Math.max(0, width - tw - cells(left))) + clip(tail, tw, false), role,
            List.copyOf(spans), current));
      }
      hits = out;
      return List.copyOf(out);
    }
    public void draw(Canvas c, Rect r, boolean ascii) {
      if (!opened)
        return;
      c.fill(r, "surface");
      var rows = layout(r.width(), r.height(), ascii);
      for (int y = 0; y < rows.size(); y++) {
        var row = rows.get(y);
        c.fill(new Rect(r.x(), r.y() + y, r.width(), 1), row.role());
        if (row.spans().isEmpty())
          c.write(r.x(), r.y() + y, row.text(), row.role(), false, r.width());
        for (var s : row.spans())
          c.write(r.x() + s.start(), r.y() + y, s.text(), s.role(), false, s.width());
      }
    }
    /** Paint a host-positioned popup and return the content rectangle for hits. */
    public Rect drawPopup(Canvas c, Rect r, String title, int padding, boolean ascii) {
      if (!opened)
        return new Rect(r.x(), r.y(), 0, 0);
      var inner = c.panel(r, title, false, ascii);
      padding = Math.max(0, Math.min(4096, padding));
      int px = Math.min(padding, inner.width() / 2), py = Math.min(padding, inner.height() / 2);
      var content = new Rect(inner.x() + px, inner.y() + py, Math.max(0, inner.width() - 2 * px),
          Math.max(0, inner.height() - 2 * py));
      draw(c, content, ascii);
      return content;
    }
    public MenuBarLayout barLayout(int width) {
      width = Math.max(0, Math.min(65535, width));
      if (width < 3)
        return new MenuBarLayout(List.of(), false, false);
      var ids = new ArrayList<String>();
      for (String id : childIds(""))
        if (!index.get(id).separator)
          ids.add(id);
      if (ids.isEmpty())
        return new MenuBarLayout(List.of(), false, false);
      int target = Math.max(0, ids.indexOf(bar));
      barFirst = Math.min(barFirst, target);
      int[] sizes = new int[ids.size()];
      for (int n = 0; n < ids.size(); n++)
        sizes[n] = Math.min(24, cells(label(index.get(ids.get(n)))) + 2);
      while (barFirst < target && sum(sizes, barFirst, target) > width - 2) barFirst++;
      while (barFirst > 0 && sum(sizes, barFirst - 1, target) <= width - 2) barFirst--;
      int x = 1, last = barFirst;
      var out = new ArrayList<MenuBarCell>();
      for (int n = barFirst; n < ids.size(); n++) {
        if (x >= width - 1)
          break;
        var i = index.get(ids.get(n));
        int w = Math.min(sizes[n], width - 1 - x);
        boolean current = i.id.equals(bar);
        String role = i.disabled ? "disabled" : current ? "selection" : "header";
        out.add(new MenuBarCell(i.id, clip(" " + label(i) + " ", w, true), role, x, w, current));
        x += w;
        last = n + 1;
      }
      return new MenuBarLayout(List.copyOf(out), barFirst > 0, last < ids.size());
    }
    private static int sum(int[] values, int a, int b) {
      int sum = 0;
      for (int n = a; n <= b; n++) sum += values[n];
      return sum;
    }
    public MenuEvent barClick(int x, int width) {
      if (x < 0 || x >= width)
        return new MenuEvent();
      var l = barLayout(width);
      if (x == 0 && l.previous())
        return handleBar("previous", "");
      if (x + 1 == width && l.next())
        return handleBar("next", "");
      for (var c : l.cells())
        if (x >= c.start() && x < c.start() + c.width() && usable(c.id(), "")) {
          bar = c.id();
          return new MenuEvent("open_request", c.id(), "");
        }
      return new MenuEvent();
    }
    public void drawBar(Canvas c, Rect r) {
      if (r.height() <= 0)
        return;
      c.fill(new Rect(r.x(), r.y(), r.width(), 1), "surface");
      var l = barLayout(r.width());
      for (var cell : l.cells()) {
        c.fill(new Rect(r.x() + cell.start(), r.y(), cell.width(), 1), cell.role());
        c.write(r.x() + cell.start(), r.y(), cell.text(), cell.role(), false, cell.width());
      }
      if (l.previous())
        c.write(r.x(), r.y(), "<", "hint", false, 1);
      if (l.next())
        c.write(r.x() + r.width() - 1, r.y(), ">", "hint", false, 1);
    }
  }
  public static Rect menuPlacement(Rect anchor, Rect viewport, int width, int height) {
    long vw = Math.max(0, viewport.width()), vh = Math.max(0, viewport.height()),
         w = Math.min(Math.max(0, width), vw), h = Math.min(Math.max(0, height), vh),
         x = Math.max(viewport.x(), Math.min((long) viewport.x() + vw - w, anchor.x())),
         y = (long) anchor.y() + Math.max(0, anchor.height());
    if (y + h > (long) viewport.y() + vh)
      y = (long) anchor.y() - h;
    y = Math.max(viewport.y(), Math.min((long) viewport.y() + vh - h, y));
    return new Rect((int) x, (int) y, (int) w, (int) h);
  }
  public static final class NoticeAction {
    public String id, label;
    public boolean disabled;
    public NoticeAction(String id) {
      this(id, "");
    }
    public NoticeAction(String id, String label) {
      this.id = id;
      this.label = label;
    }
  }
  public static final class Notice {
    public String id, text, detail = "", severity = "info";
    public int priority;
    public long expiresAt;
    public boolean persistent;
    public List<NoticeAction> actions = new ArrayList<>();
    public Notice(String id) {
      this(id, "");
    }
    public Notice(String id, String text) {
      this.id = id;
      this.text = text;
    }
  }
  public record NoticeEvent(String kind, String id, String action) {
    public NoticeEvent() {
      this("", "", "");
    }
  }
  public record FeedbackSpan(
      int start, int width, String text, String role, String action, boolean disabled) {}
  public record
      FeedbackRow(String id, String text, String role, boolean focused, List<FeedbackSpan> spans) {
    public FeedbackRow {
      spans = List.copyOf(spans);
    }
    public FeedbackRow(String id, String text, String role) {
      this(id, text, role, false, List.of());
    }
  }
  private static void feedbackNumber(long n) {
    if (n < 0 || n > 9007199254740991L)
      throw new IllegalArgumentException("expected a nonnegative safe integer");
  }
  private static int noticeSeverity(String s) {
    if (s == null)
      return -1;
    return switch (s) {
      case "info" -> 0;
      case "success" -> 1;
      case "warning" -> 2;
      case "error" -> 3;
      default -> -1;
    };
  }
  private static void feedbackDraw(Canvas c, Rect r, List<FeedbackRow> rows) {
    c.fill(r, "surface");
    for (int y = 0; y < Math.max(0, r.height()) && y < rows.size(); y++) {
      var row = rows.get(y);
      c.write(r.x(), r.y() + y, row.text(), row.role(), false, r.width());
      for (var s : row.spans())
        c.write(r.x() + s.start(), r.y() + y, s.text(), s.role(), false, s.width());
    }
  }
  /** Copied notices, host clocks and requests; no timers or business callbacks. */
  public static final class NoticeQueue {
    private final int capacity;
    private final ArrayList<Notice> source = new ArrayList<>();
    private List<FeedbackRow> hits = List.of();
    private int width;
    public String focused = "";
    public NoticeQueue() {
      this(10);
    }
    public NoticeQueue(int capacity) {
      if (capacity < 1 || capacity > 65536)
        throw new IllegalArgumentException("notice capacity must be 1..65536");
      this.capacity = capacity;
    }
    public int capacity() {
      return capacity;
    }
    private static Notice copy(Notice source) {
      var n = new Notice(source.id, source.text);
      n.detail = source.detail;
      n.severity = source.severity;
      n.priority = source.priority;
      n.expiresAt = source.expiresAt;
      n.persistent = source.persistent;
      for (var a : source.actions) {
        var owned = new NoticeAction(a.id, a.label);
        owned.disabled = a.disabled;
        n.actions.add(owned);
      }
      return n;
    }
    private static boolean pinned(Notice n) {
      return n.persistent || "error".equals(n.severity) || !n.actions.isEmpty();
    }
    private static boolean expired(Notice n, long now) {
      return !pinned(n) && n.expiresAt > 0 && n.expiresAt <= now;
    }
    public List<Notice> items() {
      return source.stream().map(NoticeQueue::copy).toList();
    }
    public void push(Notice original) {
      if (original.id == null || original.id.isEmpty() || noticeSeverity(original.severity) < 0)
        throw new IllegalArgumentException("invalid notice ID or severity");
      feedbackNumber(original.expiresAt);
      var ids = new HashSet<String>();
      if (original.actions.size() > 1024)
        throw new IllegalArgumentException("too many notice actions");
      for (var a : original.actions)
        if (a.id == null || a.id.isEmpty() || !ids.add(a.id))
          throw new IllegalArgumentException("invalid notice action");
      var n = copy(original);
      for (int i = 0; i < source.size(); i++)
        if (source.get(i).id.equals(n.id)) {
          source.set(i, n);
          hits = List.of();
          return;
        }
      if (source.size() >= capacity) {
        int at = -1;
        for (int i = 0; i < source.size(); i++) {
          var old = source.get(i);
          if (pinned(old))
            continue;
          if (at < 0 || noticeSeverity(old.severity) < noticeSeverity(source.get(at).severity)
              || noticeSeverity(old.severity) == noticeSeverity(source.get(at).severity)
                  && old.priority < source.get(at).priority)
            at = i;
        }
        if (at < 0)
          throw new IllegalArgumentException("notice queue full; important notices retained");
        var old = source.get(at);
        if (noticeSeverity(old.severity) > noticeSeverity(n.severity)
            || noticeSeverity(old.severity) == noticeSeverity(n.severity)
                && old.priority > n.priority)
          throw new IllegalArgumentException("notice queue full");
        if (focused.equals(old.id))
          focused = "";
        source.remove(at);
      }
      if (focused.isEmpty() || "error".equals(n.severity))
        focused = n.id;
      source.add(n);
      hits = List.of();
    }
    public List<Notice> visible() {
      return visible(0);
    }
    public List<Notice> visible(long now) {
      feedbackNumber(now);
      var out = new ArrayList<Notice>();
      for (var n : source)
        if (!expired(n, now))
          out.add(copy(n));
      out.sort((a, b) -> {
        int rank = Integer.compare(noticeSeverity(b.severity), noticeSeverity(a.severity));
        return rank != 0 ? rank : Integer.compare(b.priority, a.priority);
      });
      return List.copyOf(out);
    }
    public boolean dismiss(String id) {
      for (int i = 0; i < source.size(); i++)
        if (source.get(i).id.equals(id)) {
          source.remove(i);
          if (focused.equals(id))
            focused = "";
          hits = List.of();
          return true;
        }
      return false;
    }
    public List<NoticeEvent> expire(long now) {
      feedbackNumber(now);
      var out = new ArrayList<NoticeEvent>();
      for (var n : source)
        if (expired(n, now))
          out.add(new NoticeEvent("expired", n.id, ""));
      for (var e : out) dismiss(e.id());
      return List.copyOf(out);
    }
    private static int limit(int count, int height) {
      height = Math.max(0, Math.min(4096, height));
      return count > height && height > 0 ? Math.max(1, height - 1) : height;
    }
    public NoticeEvent requestAction(String id, String action, long now) {
      for (var n : visible(now))
        if (n.id.equals(id))
          for (var a : n.actions)
            if (a.id.equals(action) && !a.disabled)
              return new NoticeEvent("action", id, action);
      return new NoticeEvent();
    }
    public NoticeEvent handle(String action, long now, int height) {
      if (action.equals("up"))
        action = "previous";
      if (action.equals("down"))
        action = "next";
      var all = visible(now);
      var items = all.subList(0, Math.min(all.size(), limit(all.size(), height)));
      if (items.isEmpty() || !List.of("next", "previous", "activate", "dismiss").contains(action))
        return new NoticeEvent();
      int at = 0;
      for (int i = 0; i < items.size(); i++)
        if (items.get(i).id.equals(focused))
          at = i;
      if (action.equals("next"))
        at = Math.min(at + 1, items.size() - 1);
      else if (action.equals("previous"))
        at = Math.max(0, at - 1);
      var n = items.get(at);
      focused = n.id;
      if (action.equals("dismiss"))
        return new NoticeEvent("dismiss", n.id, "");
      if (action.equals("activate"))
        for (var a : n.actions)
          if (!a.disabled)
            return new NoticeEvent("action", n.id, a.id);
      return new NoticeEvent();
    }
    public List<FeedbackRow> layout(int width, int height, long now) {
      this.width = width = Math.max(0, Math.min(65535, width));
      height = Math.max(0, Math.min(4096, height));
      var items = visible(now);
      int count = limit(items.size(), height);
      var rows = new ArrayList<FeedbackRow>();
      for (var n : items.subList(0, Math.min(items.size(), count))) {
        String mark = switch (n.severity) {
          case "error" -> "[!]";
          case "warning" -> "[?]";
          case "success" -> "[+]";
          default -> "[i]";
        };
        String value = (focused.equals(n.id) ? "> " : "  ") + mark + " " + clean(n.text);
        if (!n.detail.isEmpty())
          value += " / " + clean(n.detail);
        var parts = new ArrayList<FeedbackSpan>();
        for (var a : n.actions) {
          String part = " [" + clean(a.label) + "]";
          parts.add(new FeedbackSpan(
              cells(value), 0, part, a.disabled ? "disabled" : n.severity, a.id, a.disabled));
          value += part;
        }
        int end = cells(value) > width ? Math.max(0, width - 1) : width;
        var spans = new ArrayList<FeedbackSpan>();
        for (var part : parts) {
          String painted = clip(part.text(), Math.max(0, end - part.start()), false);
          int size = cells(painted);
          if (size > 0)
            spans.add(new FeedbackSpan(
                part.start(), size, painted, part.role(), part.action(), part.disabled()));
        }
        rows.add(new FeedbackRow(
            n.id, clip(value, width, true), n.severity, focused.equals(n.id), spans));
      }
      if (items.size() > count && height > rows.size())
        rows.add(new FeedbackRow("", clip("+" + (items.size() - count), width, true), "hint"));
      hits = List.copyOf(rows);
      return hits;
    }
    public NoticeEvent click(int x, int y, long now) {
      feedbackNumber(now);
      if (x < 0 || x >= width || y < 0 || y >= hits.size())
        return new NoticeEvent();
      var row = hits.get(y);
      if (row.id().isEmpty() || visible(now).stream().noneMatch(n -> n.id.equals(row.id())))
        return new NoticeEvent();
      for (var s : row.spans())
        if (x >= s.start() && x < s.start() + s.width()) {
          if (s.disabled())
            return new NoticeEvent();
          focused = row.id();
          return requestAction(row.id(), s.action(), now);
        }
      focused = row.id();
      return new NoticeEvent("focus", row.id(), "");
    }
    public void draw(Canvas c, Rect r, long now) {
      feedbackDraw(c, r, layout(r.width(), r.height(), now));
    }
  }
  public static final class Progress {
    public String id = "", label = "", status = "loading", message = "", cancelLabel = "";
    public long current, total;
    public boolean cancellable;
    public Progress() {}
    public Progress(String id) {
      this.id = id;
    }
    public NoticeEvent requestCancel() {
      return !id.isEmpty() && cancellable && (status.isEmpty() || status.equals("loading"))
          ? new NoticeEvent("cancel", id, "")
          : new NoticeEvent();
    }
    public List<FeedbackRow> layout(int width, long frame) {
      feedbackNumber(current);
      feedbackNumber(total);
      feedbackNumber(frame);
      width = Math.max(0, Math.min(65535, width));
      String state = status.isEmpty() ? "loading" : status;
      String role = switch (state) {
        case "error" -> "error";
        case "success" -> "success";
        case "empty", "cancelled" -> "hint";
        case "ready" -> "body";
        case "loading" -> "info";
        default -> "error";
      };
      String value = state;
      if (state.equals("loading")) {
        if (total == 0)
          value = String.valueOf("|/-\\".charAt((int) (frame % 4)));
        else {
          double ratio = (double) Math.min(current, total) / total;
          int size = Math.min(30, Math.max(0, width - 10)), done = (int) (ratio * size);
          value = "["
              + "#".repeat(done) + "-".repeat(size - done) + "] " + (int) (ratio * 100) + "%";
        }
      }
      if (!message.isEmpty())
        value += " " + message;
      var rows = new ArrayList<FeedbackRow>();
      rows.add(new FeedbackRow(id, clip(label, width, true), role));
      rows.add(new FeedbackRow(id, clip(value, width, true), role));
      if (!requestCancel().kind().isEmpty() && !cancelLabel.isEmpty())
        rows.add(new FeedbackRow(id, clip(cancelLabel, width, true), "hint"));
      return List.copyOf(rows);
    }
    public void draw(Canvas c, Rect r, long frame) {
      feedbackDraw(c, r, layout(r.width(), frame));
    }
  }
  public static final class DataState {
    public String kind, text, detail;
    public DataState() {
      this("empty", "", "");
    }
    public DataState(String kind, String text, String detail) {
      this.kind = kind;
      this.text = text;
      this.detail = detail;
    }
    public List<FeedbackRow> layout(int width) {
      width = Math.max(0, Math.min(65535, width));
      String role = switch (kind) {
        case "ready" -> "body";
        case "loading" -> "info";
        case "empty" -> "hint";
        default -> "error";
      };
      return List.of(new FeedbackRow("", clip(text, width, true), role),
          new FeedbackRow("", clip(detail, width, true), "hint"));
    }
    public void draw(Canvas c, Rect r) {
      feedbackDraw(c, r, layout(r.width()));
    }
  }
  private static int layoutExtent(int value, int maximum) {
    if (value < 0 || value > maximum)
      throw new IllegalArgumentException("invalid layout extent");
    return value;
  }
  private static void layoutRect(Rect r) {
    for (int value : new int[] {r.x(), r.y(), r.width(), r.height()})
      layoutExtent(value, 1000000000);
  }
  public record SpacingTokens(int gap, int padding, int controlGap, int compactBelow) {
    public SpacingTokens() {
      this(0, 0, 1, 80);
    }
    public SpacingTokens(int gap, int padding, int controlGap) {
      this(gap, padding, controlGap, 80);
    }
    public static SpacingTokens forWidth(String density, int columns) {
      layoutExtent(columns, 1000000000);
      if (!List.of("auto", "compact", "comfortable").contains(density))
        throw new IllegalArgumentException("invalid density");
      return density.equals("compact") || density.equals("auto") && columns < 80
          ? new SpacingTokens()
          : new SpacingTokens(2, 1, 2);
    }
  }
  public static Rect insetRect(Rect r, int padding) {
    layoutRect(r);
    layoutExtent(padding, 1024);
    return new Rect(r.x() + Math.min(padding, r.width()), r.y() + Math.min(padding, r.height()),
        Math.max(0, r.width() - 2 * padding), Math.max(0, r.height() - 2 * padding));
  }
  public record StackItem(String id, int min, int preferred, int weight) {
    public StackItem(String id) {
      this(id, 1, 0, 1);
    }
  }
  public record StackSlot(String id, int start, int size) {}
  public record StackResult(List<StackSlot> slots, List<String> hidden, int gap) {
    public StackResult {
      slots = List.copyOf(slots);
      hidden = List.copyOf(hidden);
    }
  }
  public static StackResult stackLayout(List<StackItem> items, int total, int gap) {
    layoutExtent(total, 1000000000);
    layoutExtent(gap, 1024);
    if (items.size() > 1024)
      throw new IllegalArgumentException("too many stack items");
    var ids = new HashSet<String>();
    int minimum = 0;
    for (var i : items) {
      if (i.id() == null || i.id().isEmpty() || !ids.add(i.id())
          || layoutExtent(i.min(), 1000000) == 0)
        throw new IllegalArgumentException("invalid stack minimum/ID");
      layoutExtent(i.preferred(), 1000000);
      layoutExtent(i.weight(), 1000000);
      minimum += i.min();
    }
    if (items.isEmpty())
      return new StackResult(List.of(), List.of(), 0);
    int gaps = gap * (items.size() - 1);
    if (gaps > total || total - gaps < minimum)
      gap = 0;
    int available = total - gap * (items.size() - 1);
    int[] sizes = new int[items.size()];
    boolean[] active = new boolean[items.size()];
    for (int n = 0; n < items.size(); n++) {
      var i = items.get(n);
      if (i.min() > available && n > 0)
        continue;
      sizes[n] = Math.min(i.min(), available);
      available -= sizes[n];
      active[n] = true;
    }
    for (int n = 0; n < items.size(); n++)
      if (active[n]) {
        int add = Math.min(Math.max(0, items.get(n).preferred() - sizes[n]), available);
        sizes[n] += add;
        available -= add;
      }
    long weights = 0;
    for (int n = 0; n < items.size(); n++)
      if (active[n])
        weights += items.get(n).weight();
    if (weights > 0) {
      int extra = available;
      for (int n = 0; n < items.size(); n++)
        if (active[n]) {
          int add = (int) ((long) extra * items.get(n).weight() / weights);
          sizes[n] += add;
          available -= add;
        }
      for (int n = 0; n < items.size(); n++)
        if (available > 0 && active[n] && items.get(n).weight() > 0) {
          sizes[n]++;
          available--;
        }
    }
    var slots = new ArrayList<StackSlot>();
    var hidden = new ArrayList<String>();
    int start = 0, visible = 0;
    for (int n = 0; n < items.size(); n++) {
      var item = items.get(n);
      if (sizes[n] == 0)
        hidden.add(item.id());
      else {
        if (visible > 0)
          start += gap;
        visible++;
      }
      slots.add(new StackSlot(item.id(), start, sizes[n]));
      start += sizes[n];
    }
    return new StackResult(slots, hidden, gap);
  }
  public record NamedRect(String id, Rect rect) {}
  public record LayoutResult(List<NamedRect> rects, List<String> hidden) {
    public LayoutResult {
      rects = List.copyOf(rects);
      hidden = List.copyOf(hidden);
    }
  }
  public static LayoutResult stackRects(
      Rect parent, List<StackItem> items, SpacingTokens tokens, boolean vertical) {
    var inner = insetRect(parent, tokens.padding());
    var result = stackLayout(items, vertical ? inner.height() : inner.width(), tokens.gap());
    var rects = new ArrayList<NamedRect>();
    var hidden = new ArrayList<String>();
    for (var s : result.slots()) {
      var r = vertical ? new Rect(inner.x(), inner.y() + s.start(), inner.width(), s.size())
                       : new Rect(inner.x() + s.start(), inner.y(), s.size(), inner.height());
      rects.add(new NamedRect(s.id(), r));
      if (r.width() == 0 || r.height() == 0)
        hidden.add(s.id());
    }
    return new LayoutResult(rects, hidden);
  }
  public record DrawerPlacement(Rect rect, boolean overlay) {}
  public static DrawerPlacement drawerLayout(Rect parent, int preferred, int minContent) {
    layoutRect(parent);
    layoutExtent(preferred, 1000000000);
    layoutExtent(minContent, 1000000000);
    return new DrawerPlacement(
        new Rect(parent.x(), parent.y(), Math.min(parent.width(), preferred), parent.height()),
        parent.width() < preferred + minContent);
  }
  public static final class Badge {
    public String id = "", label = "";
    public Long count;
    public long limit = 99;
    public State state = new State();
    public FeedbackRow line(int width) {
      layoutExtent(width, 65535);
      feedbackNumber(limit);
      String text = label;
      if (count != null) {
        feedbackNumber(count);
        long cap = limit == 0 ? 99 : limit;
        text += " [" + (count > cap ? cap + "+" : Long.toString(count)) + "]";
      }
      String markers = state.markers();
      if (markers.startsWith("-"))
        markers = markers.substring(1);
      return new FeedbackRow(id, clip(markers + text, width, true), state.role());
    }
    public void draw(Canvas c, Rect r) {
      feedbackDraw(c, r, List.of(line(Math.max(0, r.width()))));
    }
  }
  public static final class Chip {
    public String id = "", label = "";
    public State state = new State();
    public boolean removable;
    public Chip() {}
    public Chip(String id, String label) {
      this.id = id;
      this.label = label;
    }
    public FeedbackRow line(int width) {
      layoutExtent(width, 65535);
      String markers = state.markers();
      if (markers.startsWith("-"))
        markers = markers.substring(1);
      String prefix = markers + "[", suffix = removable ? "] x" : "]";
      String text = clip(
          prefix + clip(label, Math.max(0, width - cells(prefix) - cells(suffix)), true) + suffix,
          width, true);
      var spans = new ArrayList<FeedbackSpan>();
      if (removable && text.endsWith(" x"))
        spans.add(new FeedbackSpan(cells(text) - 1, 1, "x",
            state.editable() ? state.role() : "disabled", "remove", !state.editable()));
      return new FeedbackRow(id, text, state.role(), false, spans);
    }
    public Event requestRemove() {
      return !id.isEmpty() && removable && state.editable() ? new Event("remove", id) : new Event();
    }
    public void draw(Canvas c, Rect r) {
      feedbackDraw(c, r, List.of(line(Math.max(0, r.width()))));
    }
  }
  public static final class Shortcut {
    public String key, text;
    public int priority;
    public boolean disabled;
    public Shortcut(String key, String text) {
      this.key = key;
      this.text = text;
    }
  }
  private static boolean layoutSpace(int cp) {
    return cp >= 9 && cp <= 13 || cp == 32 || cp == 0x85 || cp == 0xa0 || cp == 0x1680
        || cp >= 0x2000 && cp <= 0x200a || cp == 0x2028 || cp == 0x2029 || cp == 0x202f
        || cp == 0x205f || cp == 0x3000;
  }
  private static String shortcutKey(String key) {
    int[] points = clean(key).codePoints().toArray();
    int start = 0, end = points.length;
    while (start < end && layoutSpace(points[start])) start++;
    while (end > start && layoutSpace(points[end - 1])) end--;
    return fold(new String(points, start, end - start));
  }
  /** Literal hints only; applications own bindings and context-specific contents. */
  public static final class Help {
    private final List<Shortcut> items;
    public Help(List<Shortcut> source) {
      if (source.size() > 65536)
        throw new IllegalArgumentException("too many shortcuts");
      var keys = new HashSet<String>();
      var owned = new ArrayList<Shortcut>();
      for (var i : source) {
        String key = shortcutKey(i.key);
        if (key.isEmpty() || !keys.add(key))
          throw new IllegalArgumentException("empty or duplicate shortcut");
        var s = new Shortcut(i.key, i.text);
        s.priority = i.priority;
        s.disabled = i.disabled;
        owned.add(s);
      }
      owned.sort((a, b) -> Integer.compare(b.priority, a.priority));
      items = List.copyOf(owned);
    }
    public List<FeedbackRow> layout(int width, int height) {
      layoutExtent(width, 65535);
      layoutExtent(height, 4096);
      int limit = items.size() > height && height > 1 ? height - 1 : height;
      var rows = new ArrayList<FeedbackRow>();
      for (var s : items.subList(0, Math.min(items.size(), limit)))
        rows.add(new FeedbackRow(
            "", clip("[" + s.key + "] " + s.text, width, true), s.disabled ? "disabled" : "body"));
      if (items.size() > limit && height > rows.size())
        rows.add(new FeedbackRow("", clip("+" + (items.size() - limit), width, true), "hint"));
      return List.copyOf(rows);
    }
    public void draw(Canvas c, Rect r) {
      feedbackDraw(c, r, layout(Math.max(0, r.width()), Math.max(0, r.height())));
    }
  }
  public static final class Track {
    public int min, max, fixed, weight;
    public Track() {}
    public Track(int min, int max, int fixed, int weight) {
      this.min = min;
      this.max = max;
      this.fixed = fixed;
      this.weight = weight;
    }
    Track copy() {
      return new Track(min, max, fixed, weight);
    }
  }
  public static final class LayoutItem {
    public String id, drawer = "";
    public Track track = new Track();
    public int row, column, rowSpan, columnSpan;
    public boolean hidden, disabled, modal, centered;
    public Rect area = new Rect(0, 0, 0, 0);
    public LayoutItem(String id) {
      this.id = id;
    }
    LayoutItem copy() {
      var i = new LayoutItem(id);
      i.drawer = drawer;
      i.track = track.copy();
      i.row = row;
      i.column = column;
      i.rowSpan = rowSpan;
      i.columnSpan = columnSpan;
      i.hidden = hidden;
      i.disabled = disabled;
      i.modal = modal;
      i.centered = centered;
      i.area = area;
      return i;
    }
  }
  public static final class ContainerOptions {
    public String kind = "row";
    public int gap, padding, virtualWidth, virtualHeight;
    public List<Track> rows = new ArrayList<>(), columns = new ArrayList<>();
    ContainerOptions copy() {
      var o = new ContainerOptions();
      o.kind = kind;
      o.gap = gap;
      o.padding = padding;
      o.virtualWidth = virtualWidth;
      o.virtualHeight = virtualHeight;
      o.rows = rows.stream().map(Track::copy).toList();
      o.columns = columns.stream().map(Track::copy).toList();
      return o;
    }
  }
  private static void containerNumber(int n, int max) {
    if (n < 0 || n > max)
      throw new IllegalArgumentException("invalid container constraints");
  }
  private static void containerTrack(Track t) {
    for (int n : new int[] {t.min, t.max, t.fixed, t.weight}) containerNumber(n, 1000000);
    if (t.max > 0 && (t.max < t.min || t.fixed > t.max))
      throw new IllegalArgumentException("invalid track maximum");
  }
  private record TrackAllocation(int[] sizes, int gap) {}
  private static TrackAllocation allocateTracks(List<Track> input, int total, int gap) {
    if (input.isEmpty())
      return new TrackAllocation(new int[0], 0);
    var tracks = input.stream().map(Track::copy).toList();
    for (var t : tracks)
      if (t.min == 0 && t.max == 0 && t.fixed == 0 && t.weight == 0)
        t.weight = 1;
    gap = Math.min(gap, total / tracks.size());
    int available = total - gap * (tracks.size() - 1);
    long minimum = 0;
    for (var t : tracks) minimum += Math.max(t.min, t.fixed);
    if (minimum > available) {
      gap = 0;
      available = total;
    }
    var sizes = new int[tracks.size()];
    for (int n = 0; n < sizes.length; n++) {
      var t = tracks.get(n);
      sizes[n] = Math.min(available, Math.max(t.min, t.fixed));
      available -= sizes[n];
    }
    while (available > 0) {
      long weight = 0;
      for (int n = 0; n < sizes.length; n++) {
        var t = tracks.get(n);
        if (t.fixed == 0 && t.weight > 0 && (t.max == 0 || sizes[n] < t.max))
          weight += t.weight;
      }
      if (weight == 0)
        break;
      int budget = available;
      for (int n = 0; n < sizes.length; n++) {
        var t = tracks.get(n);
        if (t.fixed > 0 || t.weight == 0 || t.max > 0 && sizes[n] >= t.max)
          continue;
        int add = Math.min(available, Math.max(1, (int) ((long) budget * t.weight / weight)));
        if (t.max > 0)
          add = Math.min(add, t.max - sizes[n]);
        sizes[n] += add;
        available -= add;
      }
    }
    return new TrackAllocation(sizes, gap);
  }
  public static List<NamedRect> computeContainer(
      Rect bounds, List<LayoutItem> items, ContainerOptions o) {
    for (int v : new int[] {
             bounds.x, bounds.y, bounds.width, bounds.height, o.virtualWidth, o.virtualHeight})
      containerNumber(v, 1000000);
    containerNumber(o.gap, 1024);
    containerNumber(o.padding, 1024);
    if (!List.of("row", "column", "grid", "layers").contains(o.kind)
        || Math.max(items.size(), Math.max(o.rows.size(), o.columns.size())) > 1024)
      throw new IllegalArgumentException("invalid container kind/count");
    for (var t : o.rows) containerTrack(t);
    for (var t : o.columns) containerTrack(t);
    var seen = new HashSet<String>();
    for (var i : items) {
      if (i.id == null || i.id.isEmpty() || !seen.add(i.id))
        throw new IllegalArgumentException("invalid container ID");
      containerTrack(i.track);
      for (int v : new int[] {i.row, i.column, i.rowSpan, i.columnSpan, i.area.x, i.area.y,
               i.area.width, i.area.height})
        containerNumber(v, 1000000);
      if (!i.drawer.isEmpty()
          && (!o.kind.equals("layers") || i.centered
              || !List.of("left", "right").contains(i.drawer)))
        throw new IllegalArgumentException("invalid drawer");
    }
    var inner = insetRect(bounds, o.padding);
    var visible = items.stream().filter(i -> !i.hidden).toList();
    var out = new ArrayList<NamedRect>();
    if (o.kind.equals("row") || o.kind.equals("column")) {
      boolean horizontal = o.kind.equals("row");
      int total = horizontal ? inner.width : inner.height, at = 0;
      var a = allocateTracks(visible.stream().map(i -> i.track).toList(), total, o.gap);
      for (int n = 0; n < visible.size(); n++) {
        at = Math.min(at, total);
        int size = a.sizes[n];
        out.add(new NamedRect(visible.get(n).id,
            horizontal ? new Rect(inner.x + at, inner.y, size, inner.height)
                       : new Rect(inner.x, inner.y + at, inner.width, size)));
        at += size + a.gap;
      }
    } else if (o.kind.equals("grid")) {
      var widths = allocateTracks(o.columns, inner.width, o.gap);
      var heights = allocateTracks(o.rows, inner.height, o.gap);
      for (var i : visible) {
        int rs = Math.max(1, i.rowSpan), cs = Math.max(1, i.columnSpan);
        if (i.row + rs > heights.sizes.length || i.column + cs > widths.sizes.length)
          throw new IllegalArgumentException("invalid grid span");
        int x = 0, y = 0, w = widths.gap * (cs - 1), h = heights.gap * (rs - 1);
        for (int n = 0; n < i.column; n++) x += widths.sizes[n] + widths.gap;
        for (int n = 0; n < i.row; n++) y += heights.sizes[n] + heights.gap;
        for (int n = i.column; n < i.column + cs; n++) w += widths.sizes[n];
        for (int n = i.row; n < i.row + rs; n++) h += heights.sizes[n];
        out.add(new NamedRect(i.id,
            new Rect(inner.x + Math.min(x, inner.width), inner.y + Math.min(y, inner.height),
                Math.min(w, Math.max(0, inner.width - x)),
                Math.min(h, Math.max(0, inner.height - y)))));
      }
    } else {
      for (var i : visible) {
        int ax = Math.min(i.area.x, inner.width), ay = Math.min(i.area.y, inner.height),
            w = inner.width - ax, h = inner.height - ay, x = inner.x + ax, y = inner.y + ay;
        if (i.area.width > 0)
          w = Math.min(w, i.area.width);
        if (i.area.height > 0)
          h = Math.min(h, i.area.height);
        if (i.centered) {
          x = inner.x + (inner.width - w) / 2;
          y = inner.y + (inner.height - h) / 2;
        }
        if (!i.drawer.isEmpty()) {
          w = Math.min(inner.width, i.area.width == 0 ? inner.width : i.area.width);
          x = inner.x + (i.drawer.equals("right") ? inner.width - w : 0);
        }
        out.add(new NamedRect(i.id, new Rect(x, y, w, h)));
      }
    }
    return List.copyOf(out);
  }
  public static final class ContainerState {
    public String focused = "", captured = "";
    private String modal = "";
    private final Map<String, String> restore = new HashMap<>();
    public List<String> eligible(List<LayoutItem> items) {
      int start = 0;
      for (int n = 0; n < items.size(); n++)
        if (items.get(n).modal && !items.get(n).hidden)
          start = n;
      return items.subList(start, items.size())
          .stream()
          .filter(i -> !i.hidden && !i.disabled)
          .map(i -> i.id)
          .toList();
    }
    public void reconcile(List<LayoutItem> items) {
      var ids = eligible(items);
      String next = "";
      boolean oldVisible = false;
      for (var i : items)
        if (i.modal && !i.hidden) {
          next = i.id;
          if (i.id.equals(modal))
            oldVisible = true;
        }
      if (!next.equals(modal)) {
        if (!modal.isEmpty() && !oldVisible) {
          String previous = restore.remove(modal);
          int count = restore.size() + 1;
          for (int n = 0; n < count && previous != null; n++) {
            if (ids.contains(previous)) {
              focused = previous;
              break;
            }
            previous = restore.remove(previous);
          }
        }
        if (!next.isEmpty())
          restore.putIfAbsent(next, focused);
        modal = next;
      }
      if (!ids.contains(focused))
        focused = ids.isEmpty() ? "" : ids.get(0);
      if (!ids.contains(captured))
        captured = "";
    }
    public String moveFocus(List<LayoutItem> items, boolean previous) {
      reconcile(items);
      var ids = eligible(items);
      if (!ids.isEmpty())
        focused = ids.get((ids.indexOf(focused) + (previous ? ids.size() - 1 : 1)) % ids.size());
      return focused;
    }
    public String hit(List<LayoutItem> items, List<NamedRect> rects, int x, int y) {
      var ids = eligible(items);
      for (int n = rects.size() - 1; n >= 0; n--) {
        var r = rects.get(n);
        if (ids.contains(r.id) && r.rect.contains(x, y))
          return r.id;
      }
      return "";
    }
    public String pointer(List<LayoutItem> items, List<NamedRect> rects, int x, int y,
        boolean press, boolean release) {
      reconcile(items);
      var id = captured.isEmpty() ? hit(items, rects, x, y) : captured;
      if (press && !id.isEmpty()) {
        focused = id;
        captured = id;
      }
      if (release)
        captured = "";
      return id;
    }
  }
  @FunctionalInterface
  public interface ChildPainter {
    void draw(String id, Canvas child, boolean focused);
  }
  public static final class Container {
    public final ContainerState state = new ContainerState();
    public int scrollX, scrollY;
    private List<LayoutItem> items = List.of();
    private ContainerOptions options = new ContainerOptions();
    private List<NamedRect> rects = List.of();
    private Rect bounds = new Rect(0, 0, 0, 0);
    private int sx, sy;
    public Container(List<LayoutItem> items, ContainerOptions options) {
      setItems(items, options);
    }
    public Container(List<LayoutItem> items) {
      this(items, new ContainerOptions());
    }
    public List<LayoutItem> items() {
      return items.stream().map(LayoutItem::copy).toList();
    }
    public ContainerOptions options() {
      return options.copy();
    }
    public void setItems(List<LayoutItem> items) {
      setItems(items, options);
    }
    public void setItems(List<LayoutItem> input, ContainerOptions o) {
      computeContainer(new Rect(0, 0, 1, 1), input, o);
      var owned = input.stream().map(LayoutItem::copy).toList();
      var config = o.copy();
      items = owned;
      options = config;
      rects = List.of();
      bounds = new Rect(0, 0, 0, 0);
      state.reconcile(items);
      state.captured = "";
    }
    public List<NamedRect> draw(Canvas canvas, Rect bounds, ChildPainter painter) {
      for (int v : new int[] {bounds.x, bounds.y, bounds.width, bounds.height, scrollX, scrollY})
        containerNumber(v, 1000000);
      int vw = Math.max(bounds.width, options.virtualWidth),
          vh = Math.max(bounds.height, options.virtualHeight);
      if ((long) vw * vh > 1000000)
        throw new IllegalArgumentException("container virtual area exceeds limit");
      int sx = Math.min(scrollX, Math.max(0, vw - bounds.width)),
          sy = Math.min(scrollY, Math.max(0, vh - bounds.height));
      var rects = computeContainer(new Rect(0, 0, vw, vh), items, options);
      var virtual = new Canvas(vw, vh, canvas.palette, canvas.surfaceRole);
      state.reconcile(items);
      for (var named : rects) {
        var r = named.rect;
        if (r.width == 0 || r.height == 0)
          continue;
        var child = new Canvas(r.width, r.height, canvas.palette, canvas.surfaceRole);
        child.blit(virtual, r, 0, 0);
        child.clearCursor();
        boolean focused = named.id.equals(state.focused);
        painter.draw(named.id, child, focused);
        if (!focused)
          child.clearCursor();
        virtual.blit(child, new Rect(0, 0, r.width, r.height), r.x, r.y);
      }
      canvas.blit(virtual, new Rect(sx, sy, bounds.width, bounds.height), bounds.x, bounds.y);
      scrollX = sx;
      scrollY = sy;
      this.sx = sx;
      this.sy = sy;
      this.bounds = bounds;
      this.rects = rects;
      return rects;
    }
    public String pointer(int x, int y, boolean press, boolean release) {
      if (!bounds.contains(x, y) && state.captured.isEmpty())
        return "";
      return state.pointer(items, rects, x - bounds.x + sx, y - bounds.y + sy, press, release);
    }
  }

  public static final class Surface {
    public final String role;
    public Surface() {
      this("surface");
    }
    public Surface(String role) {
      this.role = role;
    }
    public void draw(Canvas canvas, Rect bounds, java.util.function.Consumer<Canvas> painter) {
      for (int v : new int[] {bounds.x, bounds.y, bounds.width, bounds.height})
        containerNumber(v, 1000000);
      var child = new Canvas(bounds.width, bounds.height, canvas.palette, role);
      painter.accept(child);
      canvas.blit(child, new Rect(0, 0, bounds.width, bounds.height), bounds.x, bounds.y);
    }
  }
  private static void popupNumber(int value, int limit) {
    if (value < 0 || value > limit)
      throw new IllegalArgumentException("invalid popup bounds/options");
  }
  private static void popupRect(Rect r) {
    popupNumber(r.x, 1000000000);
    popupNumber(r.y, 1000000000);
    popupNumber(r.width, 1000000);
    popupNumber(r.height, 1000000);
  }
  public record PopupLayout(Rect bounds, Rect card, Rect shadow) {
    public PopupLayout() {
      this(new Rect(0, 0, 0, 0), new Rect(0, 0, 0, 0), new Rect(0, 0, 0, 0));
    }
    public List<Rect> shadowRegions() {
      var s = shadow;
      var c = card;
      int sr = s.x + s.width, sb = s.y + s.height, cr = c.x + c.width, cb = c.y + c.height,
          x = Math.max(s.x, cr), y = Math.max(s.y, cb);
      return List.of(new Rect(x, s.y, Math.max(0, sr - x), Math.max(0, Math.min(sb, cb) - s.y)),
          new Rect(s.x, y, s.width, Math.max(0, sb - y)));
    }
    public boolean hit(int x, int y) {
      return card.contains(x, y);
    }
  }
  public record ShadowOptions(String mode, int offsetX, int offsetY) {
    public ShadowOptions() {
      this("off", 0, 0);
    }
    public ShadowOptions(String mode) {
      this(mode, 0, 0);
    }
    public ShadowOptions {
      if (!List.of("off", "auto", "solid", "dim").contains(mode))
        throw new IllegalArgumentException("invalid shadow mode");
      popupNumber(offsetX, 1000000);
      popupNumber(offsetY, 1000000);
    }
    private int[] offsets() {
      return mode.equals("off")          ? new int[] {0, 0}
          : offsetX == 0 && offsetY == 0 ? new int[] {1, 1}
                                         : new int[] {offsetX, offsetY};
    }
    public PopupLayout layout(Rect bounds) {
      popupRect(bounds);
      return shadowLayout(this, bounds);
    }
  }
  private static PopupLayout shadowLayout(ShadowOptions o, Rect bounds) {
    var offsets = o.offsets();
    if (bounds.width == 0 || bounds.height == 0)
      return new PopupLayout(bounds, bounds, new Rect(0, 0, 0, 0));
    int dx = Math.min(offsets[0], bounds.width - 1), dy = Math.min(offsets[1], bounds.height - 1);
    var card = new Rect(bounds.x, bounds.y, bounds.width - dx, bounds.height - dy);
    var shadow = new Rect(0, 0, 0, 0);
    if (dx != 0 || dy != 0) {
      int caps = (o.mode.equals("auto") || o.mode.equals("solid")) && dy > 0 ? 1 : 0;
      shadow = new Rect(bounds.x + dx, bounds.y + dy - caps, card.width, card.height + caps);
    }
    return new PopupLayout(bounds, card, shadow);
  }
  public static PopupLayout popupPlacement(
      Rect anchor, Rect viewport, int width, int height, ShadowOptions options) {
    popupRect(anchor);
    popupRect(viewport);
    popupNumber(width, 1000000);
    popupNumber(height, 1000000);
    var offsets = options.offsets();
    int w = width != 0 && height != 0 ? Math.min(width + offsets[0], viewport.width) : 0,
        h = width != 0 && height != 0 ? Math.min(height + offsets[1], viewport.height) : 0,
        mx = viewport.x + viewport.width - w, my = viewport.y + viewport.height - h,
        x = Math.max(viewport.x, Math.min(anchor.x, mx)), y = anchor.y + anchor.height;
    if (y > my)
      y = Math.max(0, anchor.y - h);
    return shadowLayout(options, new Rect(x, Math.max(viewport.y, Math.min(y, my)), w, h));
  }
  public static PopupLayout popupPlacement(Rect anchor, Rect viewport, int width, int height) {
    return popupPlacement(anchor, viewport, width, height, new ShadowOptions());
  }
  private static int shadowShade(int backdrop, boolean hasRGB, boolean has256) {
    var rgb = colorRGB(backdrop);
    int r = rgb[0], g = rgb[1], b = rgb[2], maximum = Math.max(r, Math.max(g, b));
    if (maximum <= 16)
      return hasRGB ? 0x1404040 : has256 ? 238 : 7;
    int factor = maximum <= 96 ? 2 : 4;
    if (hasRGB)
      return 0x1000000 | ((r * factor / 5) << 16) | ((g * factor / 5) << 8) | (b * factor / 5);
    if (has256)
      return 232 + Math.max(0, Math.min(23, ((r + g + b) * factor / 15 - 3) / 10));
    return 0;
  }
  private static void paintShadow(Canvas canvas, Rect region, PopupLayout layout,
      ShadowOptions options, boolean ascii, boolean hasRGB, boolean has256) {
    int left = Math.max(0, region.x), right = Math.min(canvas.width, region.x + region.width),
        top = Math.max(0, region.y), bottom = Math.min(canvas.height, region.y + region.height);
    if (left >= right || top >= bottom)
      return;
    canvas.clearCursor(new Rect(left, top, right - left, bottom - top));
    for (int y = top; y < bottom; y++) {
      var row = canvas.data[y];
      var backgrounds = new int[right - left];
      for (int x = left; x < right; x++)
        backgrounds[x - left] =
            row[x].owner >= 0 ? row[row[x].owner].style.background : row[x].style.background;
      if (row[left].owner >= 0)
        canvas.writeStyle(left, y, " ", row[left].style, 1);
      int end = right - 1, start = row[end].owner >= 0 ? row[end].owner : end;
      if (end + 1 < canvas.width && row[end + 1].owner == start)
        canvas.writeStyle(end, y, " ", row[end].style, 1);
      for (int x = left; x < right; x++) {
        if (options.mode.equals("dim")) {
          var s = row[x].style;
          row[x].style = new Style(s.foreground, s.background, s.bold, true, s.underline, s.italic);
          continue;
        }
        int bg = backgrounds[x - left],
            shade = options.mode.equals("solid") ? 0 : shadowShade(bg, hasRGB, has256),
            background = shade;
        String symbol = " ";
        if (ascii) {
          symbol = ".";
          background = bg;
        } else if (layout.shadow.height > layout.card.height) {
          if (y == layout.shadow.y) {
            symbol = "▄";
            background = bg;
          } else if (y == layout.shadow.y + layout.shadow.height - 1) {
            symbol = "▀";
            background = bg;
          }
        }
        canvas.writeStyle(x, y, symbol, new Style(shade, background, false, false, false), 1);
      }
    }
  }
  public static final class Shadow {
    public final ShadowOptions options;
    public Shadow() {
      this(new ShadowOptions());
    }
    public Shadow(ShadowOptions options) {
      this.options = options;
    }
    public PopupLayout draw(
        Canvas canvas, Rect bounds, java.util.function.Consumer<Canvas> painter) {
      return draw(canvas, bounds, painter, false);
    }
    public PopupLayout draw(
        Canvas canvas, Rect bounds, java.util.function.Consumer<Canvas> painter, boolean ascii) {
      popupRect(bounds);
      int x = Math.min(bounds.x, canvas.width), y = Math.min(bounds.y, canvas.height),
          right = Math.min(canvas.width, bounds.x + bounds.width),
          bottom = Math.min(canvas.height, bounds.y + bounds.height);
      var layout =
          shadowLayout(options, new Rect(x, y, Math.max(0, right - x), Math.max(0, bottom - y)));
      var working = new Canvas(canvas.width, canvas.height, canvas.palette, canvas.surfaceRole);
      working.blit(canvas, new Rect(0, 0, canvas.width, canvas.height), 0, 0);
      boolean hasRGB = false, has256 = false;
      for (String role : Data.ROLES) {
        var s = canvas.palette.style(role);
        for (int color : new int[] {s.foreground, s.background}) {
          hasRGB |= (color & 0x1000000) != 0;
          has256 |= (color & 0x1000000) == 0 && color >= 16 && color <= 255;
        }
      }
      if (!options.mode.equals("off"))
        for (var region : layout.shadowRegions())
          paintShadow(working, region, layout, options, ascii, hasRGB, has256);
      var card = layout.card;
      var child = new Canvas(card.width, card.height, canvas.palette, canvas.surfaceRole);
      child.blit(working, card, 0, 0);
      child.clearCursor();
      painter.accept(child);
      working.blit(child, new Rect(0, 0, card.width, card.height), card.x, card.y);
      canvas.blit(working, new Rect(0, 0, canvas.width, canvas.height), 0, 0);
      return layout;
    }
  }
  private static String dialogText(String value, int limit) {
    if (value == null)
      throw new IllegalArgumentException("invalid dialog text/ID");
    int size = 0;
    for (int at = 0; at < value.length();) {
      int cp = value.codePointAt(at);
      if (cp >= 0xd800 && cp <= 0xdfff)
        throw new IllegalArgumentException("invalid dialog Unicode");
      size += cp < 128 ? 1 : cp < 2048 ? 2 : cp < 65536 ? 3 : 4;
      if (size > limit)
        throw new IllegalArgumentException("dialog text/ID exceeds limit");
      at += Character.charCount(cp);
    }
    return value;
  }
  private record DialogRows(List<String> rows, boolean truncated) {}
  private static DialogRows dialogWrap(String text, int width, int limit) {
    if (text.isEmpty())
      return new DialogRows(List.of(), false);
    if (width <= 0 || limit <= 0)
      return new DialogRows(List.of(), true);
    var rows = new ArrayList<String>();
    var line = new StringBuilder();
    int used = 0;
    boolean lastBreak = false, truncated = false;
    for (String raw : graphemes(text)) {
      if (raw.equals("\r") || raw.equals("\n") || raw.equals("\r\n")) {
        if (rows.size() >= limit) {
          truncated = true;
          break;
        }
        rows.add(line.toString());
        line.setLength(0);
        used = 0;
        lastBreak = true;
        continue;
      }
      lastBreak = false;
      String g = clean(raw);
      int n = cells(g);
      if (n > width) {
        g = clip(g, width, true);
        n = cells(g);
      }
      if (used + n > width && line.length() != 0) {
        if (rows.size() >= limit) {
          truncated = true;
          break;
        }
        rows.add(line.toString());
        line.setLength(0);
        used = 0;
      }
      if (rows.size() >= limit) {
        truncated = true;
        break;
      }
      line.append(g);
      used += n;
    }
    if (!truncated && (line.length() != 0 || rows.isEmpty() || lastBreak)) {
      if (rows.size() < limit)
        rows.add(line.toString());
      else
        truncated = true;
    }
    if (truncated && !rows.isEmpty())
      rows.set(
          rows.size() - 1, clip(rows.get(rows.size() - 1), Math.max(0, width - 1), false) + "~");
    return new DialogRows(rows, truncated);
  }
  public record DialogButton(String id, String label, boolean disabled) {
    public DialogButton(String id) {
      this(id, "", false);
    }
    public DialogButton(String id, String label) {
      this(id, label, false);
    }
  }
  public record
      DialogButtonCell(String id, Rect rect, String text, boolean disabled, boolean focused) {}
  public record DialogLayout(
      List<String> body, List<DialogButtonCell> buttons, int hiddenButtons, boolean bodyTruncated) {
    public DialogLayout {
      body = List.copyOf(body);
      buttons = List.copyOf(buttons);
    }
  }
  public static final class Dialog {
    private String title = "", message = "", cancel = "", focused = "";
    private List<DialogButton> buttons = List.of();
    private record Hit(Rect rect, String id, boolean disabled) {}
    private final List<Hit> hits = new ArrayList<>();
    public Dialog() {
      this("", "", List.of(), "");
    }
    public Dialog(String title, String message, List<DialogButton> buttons) {
      this(title, message, buttons, "");
    }
    public Dialog(String title, String message, List<DialogButton> buttons, String cancelId) {
      setText(title, message);
      setButtons(buttons, cancelId);
    }
    public String title() {
      return title;
    }
    public String message() {
      return message;
    }
    public String cancelId() {
      return cancel;
    }
    public String focused() {
      return focused;
    }
    public List<DialogButton> buttons() {
      return List.copyOf(buttons);
    }
    public void setText(String title, String message) {
      var heading = dialogText(title == null ? this.title : title, 4096);
      var content = dialogText(message == null ? this.message : message, 1000000);
      this.title = heading;
      this.message = content;
      hits.clear();
    }
    public void setButtons(List<DialogButton> input) {
      setButtons(input, null);
    }
    public void setButtons(List<DialogButton> input, String cancelId) {
      if (input.size() > 1024)
        throw new IllegalArgumentException("too many dialog buttons");
      var owned = List.copyOf(input);
      var ids = new HashSet<String>();
      var eligible = new ArrayList<String>();
      for (var b : owned) {
        dialogText(b.id, 1024);
        dialogText(b.label, 4096);
        if (b.id.isEmpty() || !ids.add(b.id))
          throw new IllegalArgumentException("empty/duplicate dialog button ID");
        if (!b.disabled)
          eligible.add(b.id);
      }
      String cancel = dialogText(cancelId == null ? this.cancel : cancelId, 1024);
      if (!cancel.isEmpty() && !ids.contains(cancel))
        throw new IllegalArgumentException("unknown dialog cancel ID");
      String focus = eligible.contains(focused) ? focused
          : eligible.contains(cancel)           ? cancel
          : eligible.isEmpty()                  ? ""
                                                : eligible.get(0);
      buttons = owned;
      this.cancel = cancel;
      focused = focus;
      hits.clear();
    }
    public boolean focus(String id) {
      if (buttons.stream().noneMatch(b -> b.id.equals(id) && !b.disabled))
        return false;
      if (!focused.equals(id)) {
        focused = id;
        hits.clear();
      }
      return true;
    }
    public Event handle(String action) {
      var eligible = buttons.stream().filter(b -> !b.disabled).map(DialogButton::id).toList();
      if (action.equals("cancel"))
        return cancel.isEmpty()         ? new Event("cancel", "")
            : eligible.contains(cancel) ? new Event("cancel", cancel)
                                        : new Event();
      if (action.equals("activate"))
        return eligible.contains(focused) ? new Event("activate", focused) : new Event();
      if (eligible.isEmpty())
        return new Event();
      int at = Math.max(0, eligible.indexOf(focused));
      if (List.of("next", "right", "down").contains(action))
        at = (at + 1) % eligible.size();
      else if (List.of("previous", "left", "up").contains(action))
        at = (at + eligible.size() - 1) % eligible.size();
      else if (action.equals("home"))
        at = 0;
      else if (action.equals("end"))
        at = eligible.size() - 1;
      else
        return new Event();
      String id = eligible.get(at);
      if (id.equals(focused))
        return new Event();
      focus(id);
      return new Event("focus", id);
    }
    public DialogLayout layout(int width, int height) {
      popupNumber(width, 1000000);
      popupNumber(height, 1000000);
      if (width == 0 || height == 0)
        return new DialogLayout(List.of(), List.of(), buttons.size(), !message.isEmpty());
      record Position(DialogButton button, Rect rect) {}
      var positions = new ArrayList<Position>();
      int x = 0, y = 0, focusRow = 0;
      for (var b : buttons) {
        String label = clean(b.label.isEmpty() ? b.id : b.label);
        int w = Math.min(width, Math.max(1, cells(label) + 4));
        if (x != 0 && x + 1 + w > width) {
          x = 0;
          y++;
        }
        if (x != 0)
          x++;
        positions.add(new Position(b, new Rect(x, y, w, 1)));
        if (b.id.equals(focused))
          focusRow = y;
        x += w;
      }
      int[] rowWidths = new int[y + 1];
      for (var position : positions)
        rowWidths[position.rect.y] = position.rect.x + position.rect.width;
      int totalRows = positions.isEmpty() ? 0 : y + 1, visible = Math.min(height, totalRows),
          start = Math.max(0, focusRow + 1 - visible), available = height - visible,
          gap = !message.isEmpty() && visible > 0 && available >= 2 ? 1 : 0;
      var body = dialogWrap(message, width, available - gap);
      var result = new ArrayList<DialogButtonCell>();
      for (var p : positions) {
        var b = p.button;
        var r = p.rect;
        if (r.y < start || r.y >= start + visible)
          continue;
        String label = clean(b.label.isEmpty() ? b.id : b.label),
               text = r.width >= 6 ? "[ " + clip(label, Math.max(0, r.width - 4), true) + " ]"
                                   : clip(label, r.width, true);
        result.add(
            new DialogButtonCell(b.id, new Rect(r.x + (width - rowWidths[r.y]) / 2, height - visible + r.y - start, r.width, 1),
                text, b.disabled, b.id.equals(focused)));
      }
      return new DialogLayout(body.rows, result, buttons.size() - result.size(), body.truncated);
    }
    public DialogLayout draw(Canvas canvas, Rect bounds) {
      return draw(canvas, bounds, true, false);
    }
    public DialogLayout draw(Canvas canvas, Rect bounds, boolean focused, boolean ascii) {
      popupRect(bounds);
      hits.clear();
      int x = Math.min(bounds.x, canvas.width), y = Math.min(bounds.y, canvas.height);
      var r = new Rect(x, y, Math.max(0, Math.min(canvas.width, bounds.x + bounds.width) - x),
          Math.max(0, Math.min(canvas.height, bounds.y + bounds.height) - y));
      var inner = insetRect(canvas.panel(r, title, focused, ascii), 1);
      var layout = layout(inner.width, inner.height);
      for (int row = 0; row < layout.body.size(); row++)
        canvas.write(inner.x, inner.y + row, layout.body.get(row), "body", false, inner.width);
      for (var b : layout.buttons) {
        var box = new Rect(inner.x + b.rect.x, inner.y + b.rect.y, b.rect.width, 1);
        String role = b.disabled ? "disabled" : focused && b.focused ? "button.focus" : "button";
        canvas.fill(box, role);
        canvas.write(box.x + Math.max(0, (box.width - cells(b.text)) / 2), box.y, b.text, role,
            false, box.width);
        hits.add(new Hit(box, b.id, b.disabled));
      }
      return layout;
    }
    public Event click(int x, int y) {
      for (var hit : hits)
        if (hit.rect.contains(x, y)) {
          if (hit.disabled)
            return new Event();
          String id = hit.id;
          focus(id);
          return new Event("activate", id);
        }
      return new Event();
    }
  }
  public record DocumentRange(int start, int end) {}
  public record DocumentSpan(int start, int end, String role) {}
  public record
      DocumentGlyph(int x, String text, int index, int width, String role, boolean cursor) {}
  public record DocumentHit(int x, int index) {}
  public record
      DocumentLine(int number, String prefix, List<DocumentGlyph> glyphs, List<DocumentHit> hits) {
    public DocumentLine {
      glyphs = List.copyOf(glyphs);
      hits = List.copyOf(hits);
    }
  }
  private static final Set<String> DOCUMENT_ROLES =
      Set.of("body", "hint", "info", "success", "warning", "error", "header", "field", "selection",
          "button", "disabled", "edited", "syntax.keyword", "syntax.function", "syntax.type",
          "syntax.string", "syntax.number", "syntax.comment", "syntax.parameter");
  private static final Map<String, String> DOCUMENT_SYNTAX =
      Map.of("keyword", "info", "function", "success", "type", "header", "string", "warning",
          "number", "edited", "comment", "hint", "parameter", "error");
  public record MarkupDocument(String source, List<DocumentSpan> spans) {
    public MarkupDocument {
      spans = List.copyOf(spans);
    }
  }
  /** Explicit opt-in markup. Plain document setters never parse tags. */
  public static MarkupDocument parseMarkup(String markup) {
    dialogText(markup, 1000000);
    var source = new StringBuilder();
    var positions = new ArrayList<Integer>();
    var roles = new ArrayList<String>();
    positions.add(0);
    roles.add("body");
    var stack = new ArrayList<String>();
    stack.add("body");
    int at = 0;
    while (at < markup.length()) {
      if (markup.startsWith("[[", at)) {
        source.append('[');
        at += 2;
        continue;
      }
      if (markup.charAt(at) == '[') {
        int end = markup.indexOf(']', at);
        if (end < 0)
          throw new IllegalArgumentException("unbalanced markup");
        String tag = markup.substring(at + 1, end);
        if (tag.equals("/")) {
          if (stack.size() == 1)
            throw new IllegalArgumentException("unbalanced markup");
          stack.remove(stack.size() - 1);
        } else {
          if (!DOCUMENT_ROLES.contains(tag))
            throw new IllegalArgumentException("unknown markup role");
          stack.add(tag);
        }
        positions.add(source.length());
        roles.add(stack.get(stack.size() - 1));
        at = end + 1;
        continue;
      }
      int end = markup.indexOf('[', at);
      if (end < 0)
        end = markup.length();
      source.append(markup, at, end);
      at = end;
    }
    if (stack.size() != 1)
      throw new IllegalArgumentException("unbalanced markup");
    var spans = new ArrayList<DocumentSpan>();
    int offset = 0, which = 0, index = 0;
    for (String g : graphemes(source.toString())) {
      while (which + 1 < positions.size() && positions.get(which + 1) <= offset) which++;
      String role = roles.get(which);
      if (!role.equals("body")) {
        DocumentSpan last = spans.isEmpty() ? null : spans.get(spans.size() - 1);
        if (last != null && last.end() == index && last.role().equals(role))
          spans.set(spans.size() - 1, new DocumentSpan(last.start(), index + 1, role));
        else
          spans.add(new DocumentSpan(index, index + 1, role));
      }
      offset += g.length();
      index++;
    }
    return new MarkupDocument(source.toString(), spans);
  }
  public static final class TextDocument {
    private SyntaxBinding syntaxBinding;
    public Text buffer;
    public boolean wrap, lineNumbers;
    public int scrollX, scrollY;
    private String syntaxSource, searchSource, lastSource;
    private int lastCursor = -1, lastAnchor = -1, height;
    private boolean reveal;
    private List<DocumentSpan> styles = List.of();
    private List<DocumentRange> matches = List.of();
    private List<List<DocumentHit>> hits = List.of();
    public TextDocument() {
      this("", false);
    }
    public TextDocument(String text) {
      this(text, false);
    }
    public TextDocument(String text, boolean readOnly) {
      buffer = new Text(dialogText(text, 1000000));
      buffer.state.readOnly = readOnly;
      lineNumbers = !readOnly;
      syntaxSource = searchSource = text;
      reveal = !readOnly;
    }
    public static TextDocument editor(String text) {
      return new TextDocument(text);
    }
    public static TextDocument viewer(String text) {
      return new TextDocument(text, true);
    }
    @Override
    public String toString() {
      return "TextDocument(" + buffer + ")";
    }
    public List<DocumentSpan> syntax() {
      return styles;
    }
    public List<DocumentRange> searchMatches() {
      return matches;
    }
    public void setText(String text) {
      dialogText(text, 1000000);
      var old = buffer;
      buffer = new Text(text);
      buffer.state = copyState(old.state);
      buffer.secret = old.secret;
      styles = List.of();
      matches = List.of();
      syntaxSource = searchSource = text;
      scrollX = scrollY = 0;
      hits = List.of();
      lastSource = null;
      reveal = !buffer.state.readOnly;
      refreshSyntaxSafe();
    }
    private void range(int start, int end, int n) {
      if (start < 0 || end < start || end > n)
        throw new IllegalArgumentException("invalid document grapheme range");
    }
    public void setSyntax(List<DocumentSpan> spans) {
      if (spans.size() > 1000000)
        throw new IllegalArgumentException("too many document ranges");
      int n = graphemes(dialogText(buffer.value(), 1000000)).size();
      var copy = new ArrayList<DocumentSpan>();
      for (var s : spans) {
        range(s.start(), s.end(), n);
        if (!DOCUMENT_ROLES.contains(s.role()))
          throw new IllegalArgumentException("unknown document role");
        copy.add(s);
      }
      styles = List.copyOf(copy);
      syntaxSource = buffer.value();
    }
    public void setSearchMatches(List<DocumentRange> ranges) {
      if (ranges.size() > 1000000)
        throw new IllegalArgumentException("too many document ranges");
      int n = graphemes(dialogText(buffer.value(), 1000000)).size();
      var copy = new ArrayList<DocumentRange>();
      for (var s : ranges) {
        range(s.start(), s.end(), n);
        copy.add(s);
      }
      matches = List.copyOf(copy);
      searchSource = buffer.value();
    }
    public void setByteSyntax(List<DocumentSpan> spans) {
      var boundaries = new HashMap<Integer, Integer>();
      int offset = 0, index = 0;
      for (var g : graphemes(buffer.value())) {
        boundaries.put(offset, index++);
        offset += g.getBytes(java.nio.charset.StandardCharsets.UTF_8).length;
      }
      boundaries.put(offset, index);
      var converted = new ArrayList<DocumentSpan>();
      for (var s : spans) {
        Integer start = boundaries.get(s.start()), end = boundaries.get(s.end());
        if (start == null || end == null)
          throw new IllegalArgumentException("offset splits grapheme or outside text");
        converted.add(new DocumentSpan(start, end, s.role()));
      }
      setSyntax(converted);
    }
    public void setMarkup(String markup) {
      var parsed = parseMarkup(markup);
      setSyntaxAnalyzer(null);
      setText(parsed.source());
      setSyntax(parsed.spans());
    }
    private void applySyntax(SyntaxAnalysis analysis) {
      if (buffer.secret)
        throw new IllegalArgumentException("syntax analysis unavailable for secret buffers");
      analysis.validate(buffer.value());
      var spans = new ArrayList<DocumentSpan>();
      for (var t : analysis.tokens())
        spans.add(new DocumentSpan(t.start(), t.end(), syntaxRoleStyle(t.role())));
      setByteSyntax(spans);
    }
    public void setSyntaxAnalysis(SyntaxAnalysis analysis) {
      if (syntaxBinding != null && syntaxBinding.refreshing)
        throw new IllegalArgumentException("recursive syntax analysis");
      applySyntax(analysis);
      syntaxBinding = new SyntaxBinding(null, new SyntaxRequest(), buffer.value());
    }
    public void setSyntaxAnalyzer(SyntaxAnalyzer analyzer) {
      setSyntaxAnalyzer(analyzer, new SyntaxRequest());
    }
    public void setSyntaxAnalyzer(SyntaxAnalyzer analyzer, SyntaxRequest request) {
      if (syntaxBinding != null && syntaxBinding.refreshing)
        throw new IllegalArgumentException("recursive syntax analysis");
      if (analyzer == null) {
        syntaxBinding = null;
        styles = List.of();
        syntaxSource = buffer.value();
        return;
      }
      if (buffer.secret)
        throw new IllegalArgumentException("syntax analysis unavailable for secret buffers");
      if (request == null)
        request = new SyntaxRequest();
      var analysis = analyzer.analyzeSyntax(buffer.value(), request);
      applySyntax(analysis);
      syntaxBinding = new SyntaxBinding(analyzer, request, buffer.value());
    }
    public String syntaxError() {
      return buffer.secret || syntaxBinding == null ? null : syntaxBinding.error;
    }
    private void refreshSyntaxSafe() {
      try {
        refreshSyntax();
      } catch (RuntimeException ignored) {
      }
    }
    public void refreshSyntax() {
      var binding = syntaxBinding;
      if (buffer.secret) {
        if (binding != null) {
          binding.source = "";
          binding.dirty = true;
        }
        styles = List.of();
        return;
      }
      if (binding == null)
        return;
      if (binding.refreshing)
        throw new IllegalArgumentException("recursive syntax analysis");
      if (binding.source.equals(buffer.value()) && !binding.dirty) {
        if (binding.error != null)
          throw new IllegalArgumentException(binding.error);
        return;
      }
      String source = buffer.value();
      binding.refreshing = true;
      try {
        if (binding.analyzer != null)
          applySyntax(binding.analyzer.analyzeSyntax(source, binding.request));
        else {
          styles = List.of();
          syntaxSource = source;
        }
        binding.error = null;
      } catch (RuntimeException error) {
        styles = List.of();
        syntaxSource = buffer.value();
        binding.error =
            error.getMessage() == null ? error.getClass().getSimpleName() : error.getMessage();
        throw error;
      } finally {
        binding.source = source;
        binding.dirty = false;
        binding.refreshing = false;
      }
    }
    public void revealCursor() {
      reveal = true;
    }
    public Event handle(String action) {
      return handle(action, "");
    }
    private void validateScroll() {
      if (scrollX < 0 || scrollY < 0 || scrollX > 1000000 || scrollY > 1000000)
        throw new IllegalArgumentException("invalid document scroll position");
    }
    public Event handle(String action, String text) {
      validateScroll();
      if (buffer.state.disabled)
        return new Event("", "", "");
      int step = Math.max(1, height);
      switch (action) {
        case "page_up" -> scrollY = Math.max(0, scrollY - step);
        case "page_down" -> scrollY = (int) Math.min(1000000L, (long) scrollY + step);
        case "scroll_up" -> scrollY = Math.max(0, scrollY - 1);
        case "scroll_down" -> scrollY = (int) Math.min(1000000L, (long) scrollY + 1);
        case "scroll_left" -> scrollX = Math.max(0, scrollX - 4);
        case "scroll_right" -> scrollX = (int) Math.min(1000000L, (long) scrollX + 4);
        default -> {
          if (Set.of("insert", "paste", "newline").contains(action) && !buffer.state.readOnly) {
            String addition =
                buffer.sanitize(dialogText(action.equals("newline") ? "\n" : text, 1000000));
            int[] selected = buffer.selectionBytes();
            if (buffer.value().getBytes(java.nio.charset.StandardCharsets.UTF_8).length
                    - (selected[1] - selected[0])
                    + addition.getBytes(java.nio.charset.StandardCharsets.UTF_8).length
                > 1000000)
              throw new IllegalArgumentException("document source exceeds limit");
          }
          var e = buffer.handle(action, text);
          if (Set.of("select", "change", "cut").contains(e.kind()))
            reveal = true;
          refreshSyntaxSafe();
          return e;
        }
      }
      reveal = false;
      return new Event("scroll", "", "");
    }
    private record Item(int index, String text) {}
    private static final class Logical {
      final List<Item> items = new ArrayList<>();
      int end;
      Logical(int end) {
        this.end = end;
      }
    }
    public List<DocumentLine> layout(int width, int height) {
      validateScroll();
      if (width < 0 || height < 0 || width > 1000000 || height > 1000000)
        throw new IllegalArgumentException("invalid document dimensions");
      dialogText(buffer.value(), 1000000);
      refreshSyntaxSafe();
      this.height = height;
      hits = List.of();
      if (width == 0 || height == 0)
        return List.of();
      buffer.select(buffer.anchor, buffer.cursor);
      String source = buffer.value();
      if (!source.equals(syntaxSource)) {
        styles = List.of();
        syntaxSource = source;
      }
      if (!source.equals(searchSource)) {
        matches = List.of();
        searchSource = source;
      }
      var raw = graphemes(source);
      var shown = new ArrayList<String>();
      for (var g : raw) shown.add(buffer.secret ? "*" : g);
      String[] roles = new String[shown.size()];
      Arrays.fill(roles, "body");
      int lo = Math.min(buffer.anchor, buffer.cursor), hi = Math.max(buffer.anchor, buffer.cursor);
      if (!buffer.secret) {
        for (var s : styles)
          for (int i = s.start(); i < Math.min(s.end(), roles.length); i++) roles[i] = s.role();
        for (var s : matches)
          for (int i = s.start(); i < Math.min(s.end(), roles.length); i++) roles[i] = "edited";
      }
      for (int i = lo; i < hi; i++) roles[i] = "selection";
      if (buffer.state.disabled)
        Arrays.fill(roles, "disabled");
      var logical = new ArrayList<Logical>();
      logical.add(new Logical(0));
      for (int i = 0; i < shown.size(); i++) {
        var line = logical.get(logical.size() - 1);
        var g = shown.get(i);
        if (Set.of("\r", "\n", "\r\n").contains(g)) {
          line.end = i;
          logical.add(new Logical(i + 1));
        } else {
          line.items.add(new Item(
              i, g.codePoints().anyMatch(cp -> cp < 32 || cp >= 127 && cp < 160) ? " " : g));
          line.end = i + 1;
        }
      }
      boolean shouldReveal = reveal
          || (!source.equals(lastSource) || buffer.cursor != lastCursor
                 || buffer.anchor != lastAnchor)
              && !buffer.state.readOnly;
      if (shouldReveal && !wrap)
        for (int number = 0; number < logical.size(); number++) {
          var line = logical.get(number);
          int start = line.items.isEmpty() ? line.end : line.items.get(0).index();
          if (start <= buffer.cursor && buffer.cursor <= line.end) {
            int pw = lineNumbers ? cells((number + 1) + " ") : 0,
                available = Math.max(1, width - pw), col = 0, cw = 1;
            for (var item : line.items) {
              if (item.index() < buffer.cursor)
                col += cells(item.text());
              if (item.index() == buffer.cursor)
                cw = Math.max(1, cells(item.text()));
            }
            scrollX = Math.max(
                0, Math.max(Math.min(scrollX, col), col + Math.min(cw, available) - available));
            break;
          }
        }
      int total = 0;
      for (var g : shown) total += cells(g);
      scrollX = Math.max(0, Math.min(scrollX, total));
      var rows = new ArrayList<DocumentLine>();
      for (int number = 0; number < logical.size(); number++) {
        var line = logical.get(number);
        String prefix = lineNumbers ? clip((number + 1) + " ", width, false) : "";
        int pw = cells(prefix), available = Math.max(0, width - pw), used = 0;
        var groups = new ArrayList<List<Item>>();
        groups.add(new ArrayList<>());
        for (var item : line.items) {
          int w = cells(item.text());
          if (wrap && !groups.get(groups.size() - 1).isEmpty() && used + w > available) {
            groups.add(new ArrayList<>());
            used = 0;
          }
          groups.get(groups.size() - 1).add(item);
          used += w;
        }
        if (wrap && !groups.get(groups.size() - 1).isEmpty() && used >= available
            && line.end == buffer.cursor && !buffer.state.readOnly)
          groups.add(new ArrayList<>());
        for (int segment = 0; segment < groups.size(); segment++) {
          var group = groups.get(segment);
          int x = pw, start = group.isEmpty() ? line.end : group.get(0).index();
          var glyphs = new ArrayList<DocumentGlyph>();
          var rowHits = new ArrayList<DocumentHit>();
          rowHits.add(new DocumentHit(pw, start));
          for (var item : group) {
            int w = cells(item.text()), local = x - (wrap ? 0 : scrollX);
            rowHits.add(new DocumentHit(local, item.index()));
            if (local >= pw && local + w <= width)
              glyphs.add(new DocumentGlyph(local, item.text(), item.index(), w, roles[item.index()],
                  item.index() == buffer.cursor));
            x += w;
          }
          int finish = group.isEmpty() ? line.end : group.get(group.size() - 1).index() + 1,
              local = x - (wrap ? 0 : scrollX);
          rowHits.add(new DocumentHit(local, finish));
          if (finish == buffer.cursor && local >= pw && local < width
              && (segment == groups.size() - 1 || buffer.cursor < line.end))
            glyphs.add(new DocumentGlyph(
                local, " ", finish, 1, buffer.state.disabled ? "disabled" : "body", true));
          rows.add(new DocumentLine(number + 1, prefix, glyphs, rowHits));
        }
      }
      if (shouldReveal)
        for (int i = 0; i < rows.size(); i++)
          if (rows.get(i).glyphs().stream().anyMatch(DocumentGlyph::cursor))
            scrollY = Math.max(0, Math.max(Math.min(scrollY, i), i - height + 1));
      scrollY = Math.max(0, Math.min(scrollY, Math.max(0, rows.size() - height)));
      var visible = List.copyOf(rows.subList(scrollY, Math.min(rows.size(), scrollY + height)));
      var nextHits = new ArrayList<List<DocumentHit>>();
      for (var row : visible) nextHits.add(row.hits());
      hits = List.copyOf(nextHits);
      lastSource = source;
      lastCursor = buffer.cursor;
      lastAnchor = buffer.anchor;
      reveal = false;
      return visible;
    }
    public void draw(Canvas canvas, Rect bounds) {
      draw(canvas, bounds, true, false);
    }
    public void draw(Canvas canvas, Rect bounds, boolean focused, boolean ascii) {
      popupRect(bounds);
      String role = buffer.state.readOnly ? canvas.surfaceRole : "editor";
      canvas.fill(bounds, role);
      var rows = layout(bounds.width(), bounds.height());
      int[] cursor = null;
      for (int y = 0; y < rows.size(); y++) {
        var row = rows.get(y);
        canvas.writeStyle(bounds.x(), bounds.y() + y, row.prefix(),
            canvas.palette.textOnSurface(buffer.state.disabled ? "disabled" : "hint", role),
            bounds.width());
        for (var g : row.glyphs()) {
          Style style = g.role().startsWith("syntax.") ? syntaxStyle(canvas.palette, g.role(), role)
              : Set.of("selection", "edited", "field", "button", "header").contains(g.role())
              ? canvas.palette.style(g.role())
              : canvas.palette.textOnSurface(g.role(), role);
          canvas.writeStyle(bounds.x() + g.x(), bounds.y() + y, g.text(), style, g.width());
          if (g.cursor())
            cursor = new int[] {bounds.x() + g.x(), bounds.y() + y, g.width()};
        }
      }
      if (focused && !buffer.state.readOnly && !buffer.state.disabled && cursor != null)
        canvas.setCursor(cursor[0], cursor[1], cursor[2]);
    }
    public Event click(int x, int y, int width, int height) {
      return click(x, y, width, height, false);
    }
    public Event click(int x, int y, int width, int height, boolean extend) {
      if (buffer.state.disabled || x < 0 || y < 0 || x >= width || y >= height)
        return new Event("", "", "");
      layout(width, height);
      if (hits.isEmpty())
        return new Event("", "", "");
      var row = hits.get(Math.min(y, hits.size() - 1));
      int at = row.get(0).index();
      for (var hit : row)
        if (hit.x() <= x)
          at = hit.index();
      buffer.select(extend ? buffer.anchor : at, at);
      reveal = true;
      return new Event("select", "", "");
    }
  }
  public record SyntaxToken(int start, int end, String role) {}
  public record SyntaxRequest(String language, String dialect) {
    public SyntaxRequest() {
      this("", "");
    }
    public SyntaxRequest {
      language = dialogText(language, 128);
      dialect = dialogText(dialect, 128);
    }
  }
  public record
      SyntaxAnalysis(String source, String language, String dialect, List<SyntaxToken> tokens) {
    public SyntaxAnalysis {
      tokens = List.copyOf(tokens);
    }
    public void validate(String text) {
      dialogText(source, 1000000);
      dialogText(language, 128);
      dialogText(dialect, 128);
      if (!source.equals(text))
        throw new IllegalArgumentException("stale syntax source");
      if (tokens.size() > 1000000)
        throw new IllegalArgumentException("too many syntax tokens");
      var boundaries = new HashSet<Integer>();
      boundaries.add(0);
      int offset = 0;
      for (int at = 0; at < text.length();) {
        int cp = text.codePointAt(at);
        offset += cp < 128 ? 1 : cp < 2048 ? 2 : cp < 65536 ? 3 : 4;
        at += Character.charCount(cp);
        boundaries.add(offset);
      }
      int end = 0;
      for (var t : tokens) {
        dialogText(t.role(), 128);
        if (t.start() < end || t.end() <= t.start() || !boundaries.contains(t.start())
            || !boundaries.contains(t.end()))
          throw new IllegalArgumentException(
              "unordered, overlapping or invalid UTF-8 syntax range");
        end = t.end();
      }
    }
  }
  @FunctionalInterface
  public interface SyntaxAnalyzer {
    SyntaxAnalysis analyzeSyntax(String text, SyntaxRequest request);
  }
  private static final class SyntaxBinding {
    final SyntaxAnalyzer analyzer;
    final SyntaxRequest request;
    String source, error;
    boolean dirty, refreshing;
    SyntaxBinding(SyntaxAnalyzer analyzer, SyntaxRequest request, String source) {
      this.analyzer = analyzer;
      this.request = request;
      this.source = source;
    }
  }
  public static String syntaxRoleStyle(String role) {
    if (role == null)
      return "body";
    return switch (role) {
      case "keyword" -> "syntax.keyword";
      case "function", "macro", "attribute" -> "syntax.function";
      case "type" -> "syntax.type";
      case "string", "character" -> "syntax.string";
      case "number", "constant" -> "syntax.number";
      case "comment", "directive" -> "syntax.comment";
      case "parameter", "lifetime" -> "syntax.parameter";
      default -> "body";
    };
  }
  public static String syntaxPaletteRole(String role) {
    if (role == null)
      return "body";
    if (role.startsWith("syntax."))
      role = role.substring(7);
    return DOCUMENT_SYNTAX.getOrDefault(role, "body");
  }
  public static Style syntaxStyle(Palette palette, String role) {
    return syntaxStyle(palette, role, "editor");
  }
  public static Style syntaxStyle(Palette palette, String role, String surface) {
    String kind = role == null       ? ""
        : role.startsWith("syntax.") ? role.substring(7)
                                     : role,
           mapped = syntaxPaletteRole(kind);
    var base = palette.textOnSurface(mapped, surface);
    if (mapped.equals("body"))
      return base;
    if (palette.theme == 2)
      return new Style(base.foreground, base.background, false, false,
          Set.of("keyword", "parameter").contains(kind), kind.equals("comment"));
    boolean dark =
        palette.style("surface").background == 0 && palette.style("warning").foreground == 3;
    for (String name : Data.ROLES) {
      var s = palette.style(name);
      dark &= s.foreground >= 0 && s.foreground <= 7 && s.background >= 0 && s.background <= 7;
    }
    if (dark) {
      int foreground = Set.of("keyword", "function", "string", "parameter").contains(kind) ? 3 : 7;
      if (colorContrast(foreground, base.background) < 4.5
          && colorContrast(base.foreground, base.background)
              > colorContrast(foreground, base.background))
        foreground = base.foreground;
      return new Style(foreground, base.background, Set.of("keyword", "number").contains(kind),
          false, Set.of("keyword", "type", "parameter").contains(kind),
          Set.of("string", "comment").contains(kind));
    }
    return base;
  }
  private static boolean sqlStart(int cp) {
    return cp == '_' || inRanges(cp, SyntaxUnicodeData.ALPHABETIC);
  }
  private static boolean sqlPart(int cp) {
    return sqlStart(cp) || inRanges(cp, SyntaxUnicodeData.NUMBER) || cp == '$' || cp == '#'
        || cp >= 0x300 && cp <= 0x36f || cp >= 0x1ab0 && cp <= 0x1aff
        || cp >= 0x1dc0 && cp <= 0x1dff || cp >= 0x20d0 && cp <= 0x20ff
        || cp >= 0xfe20 && cp <= 0xfe2f;
  }
  private static boolean sqlSpace(int cp) {
    return inRanges(cp, SyntaxUnicodeData.WHITESPACE);
  }
  private static boolean sqlDigit(int cp) {
    return cp >= '0' && cp <= '9';
  }
  private static int sqlQuoted(String text, int at, char quote) {
    at++;
    while (at < text.length()) {
      if (text.charAt(at) == quote) {
        at++;
        if (at < text.length() && text.charAt(at) == quote) {
          at++;
          continue;
        }
        return at;
      }
      at++;
    }
    return at;
  }
  /** Independent optional SQL/PLSQL classification; never executes SQL. */
  public static final class SQLAnalyzer implements SyntaxAnalyzer {
    private static final Set<String> TYPES = Set.copyOf(Arrays.asList(SqlWordsData.TYPES)),
                                     FUNCTIONS = Set.copyOf(Arrays.asList(SqlWordsData.FUNCTIONS)),
                                     KEYWORDS = Set.copyOf(Arrays.asList(SqlWordsData.KEYWORDS));
    public SyntaxAnalysis analyzeSyntax(String text) {
      return analyzeSyntax(text, new SyntaxRequest());
    }
    @Override
    public SyntaxAnalysis analyzeSyntax(String text, SyntaxRequest request) {
      dialogText(text, 1000000);
      if (request == null)
        request = new SyntaxRequest();
      String language =
                 request.language().isEmpty() ? "sql" : request.language().toLowerCase(Locale.ROOT),
             dialect = request.dialect().isEmpty() ? "oracle"
                                                   : request.dialect().toLowerCase(Locale.ROOT);
      if (!Set.of("sql", "plsql").contains(language) || !dialect.equals("oracle"))
        throw new IllegalArgumentException("unsupported syntax language/dialect");
      int n = text.length(), i = 0;
      var raw = new ArrayList<SyntaxToken>();
      while (i < n) {
        int start = i, cp = text.codePointAt(i);
        if (sqlSpace(cp)) {
          i += Character.charCount(cp);
          continue;
        }
        String role = "punctuation";
        int prefix = i + 2 < n && (text.charAt(i) == 'q' || text.charAt(i) == 'Q')
                && text.charAt(i + 1) == '\''
            ? 2
            : i + 3 < n && (text.charAt(i) == 'n' || text.charAt(i) == 'N')
                && (text.charAt(i + 1) == 'q' || text.charAt(i + 1) == 'Q')
                && text.charAt(i + 2) == '\''
            ? 3
            : 0;
        if (text.startsWith("--", i)) {
          role = "comment";
          i += 2;
          while (i < n && text.charAt(i) != '\r' && text.charAt(i) != '\n') i++;
        } else if (text.startsWith("/*", i)) {
          role = "comment";
          int end = text.indexOf("*/", i + 2);
          i = end < 0 ? n : end + 2;
        } else if (prefix > 0) {
          role = "string";
          i += prefix;
          if (i < n) {
            int open = text.codePointAt(i);
            if (!sqlSpace(open)) {
              String close = switch (open) {
                case '[' -> "]";
                case '{' -> "}";
                case '(' -> ")";
                case '<' -> ">";
                default -> new String(Character.toChars(open));
              };
              String ending = close + "'";
              int end = text.indexOf(ending, i + Character.charCount(open));
              i = end < 0 ? n : end + ending.length();
            } else {
              i = start + Character.charCount(cp);
              role = "identifier";
            }
          }
        } else if (cp == '\''
            || (cp == 'n' || cp == 'N') && i + 1 < n && text.charAt(i + 1) == '\'') {
          role = "string";
          i = sqlQuoted(text, i + (cp == '\'' ? 0 : 1), '\'');
        } else if (cp == '"') {
          role = "identifier";
          i = sqlQuoted(text, i, '"');
        } else if (cp == ':' && i + 1 < n
            && (sqlStart(text.codePointAt(i + 1)) || sqlDigit(text.charAt(i + 1))
                || text.charAt(i + 1) == '"')) {
          role = "parameter";
          i++;
          if (text.charAt(i) == '"')
            i = sqlQuoted(text, i, '"');
          else
            while (i < n && sqlPart(text.codePointAt(i)))
              i += Character.charCount(text.codePointAt(i));
        } else if (text.startsWith("..", i)) {
          role = "operator";
          i += 2;
        } else if (sqlDigit(cp) || cp == '.' && i + 1 < n && sqlDigit(text.charAt(i + 1))) {
          role = "number";
          while (i < n && sqlDigit(text.charAt(i))) i++;
          if (i < n && text.charAt(i) == '.' && !text.startsWith("..", i)) {
            i++;
            while (i < n && sqlDigit(text.charAt(i))) i++;
          }
          if (i < n && (text.charAt(i) == 'e' || text.charAt(i) == 'E')) {
            int end = i + 1;
            if (end < n && (text.charAt(end) == '+' || text.charAt(end) == '-'))
              end++;
            int first = end;
            while (end < n && sqlDigit(text.charAt(end))) end++;
            if (end > first)
              i = end;
          }
          if (i < n && "fFdD".indexOf(text.charAt(i)) >= 0)
            i++;
        } else if (sqlStart(cp)) {
          i += Character.charCount(cp);
          while (i < n && sqlPart(text.codePointAt(i)))
            i += Character.charCount(text.codePointAt(i));
          var word = new StringBuilder(text.substring(start, i));
          for (int k = 0; k < word.length(); k++) {
            char c = word.charAt(k);
            if (c >= 'a' && c <= 'z')
              word.setCharAt(k, (char) (c - 32));
          }
          String upper = word.toString();
          role = TYPES.contains(upper)    ? "type"
              : FUNCTIONS.contains(upper) ? "function"
              : KEYWORDS.contains(upper)  ? "keyword"
                                          : "identifier";
        } else {
          i += Character.charCount(cp);
          if (cp < 128 && "+-*/%=<>!|:^~".indexOf(cp) >= 0) {
            role = "operator";
            if (i < n
                && Set.of(":=", "=>", "<=", ">=", "!=", "<>", "||", "**")
                    .contains(text.substring(start, i + 1)))
              i++;
          }
        }
        raw.add(new SyntaxToken(start, i, role));
      }
      var tokens = new ArrayList<SyntaxToken>();
      int which = 0, previous = -1, offset = 0, bytes = 0;
      for (String g : graphemes(text)) {
        int end = offset + g.length(),
            size = g.getBytes(java.nio.charset.StandardCharsets.UTF_8).length;
        while (which < raw.size() && raw.get(which).end() <= offset) which++;
        if (which < raw.size() && raw.get(which).start() < end) {
          SyntaxToken last = tokens.isEmpty() ? null : tokens.get(tokens.size() - 1);
          if (previous == which && last != null && last.end() == bytes)
            tokens.set(tokens.size() - 1, new SyntaxToken(last.start(), bytes + size, last.role()));
          else
            tokens.add(new SyntaxToken(bytes, bytes + size, raw.get(which).role()));
          previous = which;
        } else
          previous = -1;
        offset = end;
        bytes += size;
      }
      return new SyntaxAnalysis(text, language, dialect, tokens);
    }
  }
  public static final class GridColumn {
    public String id, label, pin = "";
    public int width = 12;
    public boolean editable, hidden;
    public GridColumn(String id) {
      this(id, id, 12, false);
    }
    public GridColumn(String id, String label, int width, boolean editable) {
      this.id = id;
      this.label = label;
      this.width = width;
      this.editable = editable;
    }
    private GridColumn copy() {
      var c = new GridColumn(id, label, width, editable);
      c.hidden = hidden;
      c.pin = pin;
      return c;
    }
  }
  public static final class GridRecord {
    public final String id;
    public final Map<String, String> cells = new LinkedHashMap<>();
    public State state = new State();
    public final Map<String, State> cellStates = new HashMap<>();
    public GridRecord(String id) {
      this.id = Objects.requireNonNull(id);
    }
    public GridRecord(String id, Map<String, String> cells) {
      this(id);
      this.cells.putAll(cells);
    }
    private GridRecord copy() {
      var r = new GridRecord(id, cells);
      r.state = copyState(state);
      cellStates.forEach((k, v) -> r.cellStates.put(k, copyState(v)));
      return r;
    }
  }
  public record GridValue(String text, boolean isNull) {
    public GridValue {
      Objects.requireNonNull(text);
    }
  }
  public interface GridSource {
    int size();
    GridRecord row(int index);
    OptionalInt indexOf(String id);
  }
  public static final class MemoryRows implements GridSource {
    private final List<GridRecord> items = new ArrayList<>();
    private final Map<String, Integer> indices = new HashMap<>();
    public MemoryRows(List<GridRecord> rows) {
      for (var r : rows) {
        dialogText(r.id, 1000000);
        if (r.cells.size() > 65536)
          throw new IllegalArgumentException("too many grid cells");
        if (r.id.isEmpty() || indices.put(r.id, items.size()) != null)
          throw new IllegalArgumentException("nonempty unique row IDs required");
        for (var v : r.cells.values())
          if (v != null)
            dialogText(v, 16 * 1024 * 1024);
        items.add(r.copy());
      }
    }
    public int size() {
      return items.size();
    }
    public GridRecord row(int i) {
      return items.get(i).copy();
    }
    public OptionalInt indexOf(String id) {
      var i = indices.get(id);
      return i == null ? OptionalInt.empty() : OptionalInt.of(i);
    }
  }
  public static final class GridOptions {
    public boolean rowNumbers, verticalLines, horizontalLines, striped, useSurface, hideHeader,
        statusBar, ascii;
    public boolean highlightCell = true, highlightRow, preserveEdited = true, showCellMarkers;
    public boolean disableKeyboard, disableMouse, disableEditing, disableCopy, disableResize,
        disableHeaderSort;
    public int padding, rowSpacing, gutterWidth, maxCopyCells = 10000;
    public String selection = "cell";
    public List<String> statusFields = new ArrayList<>(List.of(
        "position", "column", "selection", "sort", "filter", "loading", "more", "meta", "error"));
    public GridOptions copy() {
      var o = new GridOptions();
      o.rowNumbers = rowNumbers;
      o.verticalLines = verticalLines;
      o.horizontalLines = horizontalLines;
      o.striped = striped;
      o.useSurface = useSurface;
      o.hideHeader = hideHeader;
      o.statusBar = statusBar;
      o.ascii = ascii;
      o.highlightCell = highlightCell;
      o.highlightRow = highlightRow;
      o.preserveEdited = preserveEdited;
      o.showCellMarkers = showCellMarkers;
      o.disableKeyboard = disableKeyboard;
      o.disableMouse = disableMouse;
      o.disableEditing = disableEditing;
      o.disableCopy = disableCopy;
      o.disableResize = disableResize;
      o.disableHeaderSort = disableHeaderSort;
      o.padding = padding;
      o.rowSpacing = rowSpacing;
      o.gutterWidth = gutterWidth;
      o.maxCopyCells = maxCopyCells;
      o.selection = selection;
      o.statusFields = new ArrayList<>(statusFields);
      return o;
    }
    public GridOptions withDensity(String density) {
      if (!List.of("compact", "normal", "comfortable").contains(density))
        throw new IllegalArgumentException("invalid grid density");
      var o = copy();
      o.padding = density.equals("compact") ? 0 : 1;
      o.rowSpacing = density.equals("comfortable") ? 1 : 0;
      return o;
    }
  }
  public static GridOptions gridPreset(String name) {
    var o = new GridOptions();
    if (name.isEmpty() || name.equals("simple"))
      return o;
    if (!name.equals("data"))
      throw new IllegalArgumentException("unknown grid preset");
    o.rowNumbers = o.verticalLines = o.useSurface = o.statusBar = o.highlightRow =
        o.showCellMarkers = true;
    o.padding = 1;
    return o;
  }
  public static final class GridColumnOptions {
    public String align = "left", overflow = "ellipsis";
    public int minWidth = 1, maxWidth = 4096, expand;
    public boolean autoFit;
    public GridColumnOptions copy() {
      var o = new GridColumnOptions();
      o.align = align;
      o.overflow = overflow;
      o.minWidth = minWidth;
      o.maxWidth = maxWidth;
      o.expand = expand;
      o.autoFit = autoFit;
      return o;
    }
  }
  public static final class GridCellInfo {
    public String display = "", metadata = "";
    public boolean hasDisplay, isNull, numeric;
    public State state = new State();
    public GridCellInfo copy() {
      var o = new GridCellInfo();
      o.display = display;
      o.metadata = metadata;
      o.hasDisplay = hasDisplay;
      o.isNull = isNull;
      o.numeric = numeric;
      o.state = copyState(state);
      return o;
    }
  }
  public record GridRange(String anchorRow, String anchorColumn, String endRow, String endColumn) {}
  public static final class GridLabels {
    public String nullText = "NULL", loading = "loading", empty = "empty", range = "range",
                  more = "more";
    public GridLabels copy() {
      var v = new GridLabels();
      v.nullText = nullText;
      v.loading = loading;
      v.empty = empty;
      v.range = range;
      v.more = more;
      return v;
    }
  }
  public static final class GridDataStatus {
    public int totalRows;
    public String metadata = "", filter = "", error = "";
    public boolean loading, hasMore;
  }
  public record GridSpan(String id, int x, int width) {}
  public record GridGeometry(int top, int left, int gutter, int headerRows, int footerRows,
      int bodyRows, int stride, List<GridSpan> columns) {
    public GridGeometry {
      columns = List.copyOf(columns);
    }
  }
  @FunctionalInterface
  public interface GridPrepare {
    GridValue prepare(GridRecord row, GridColumn column);
  }
  @FunctionalInterface
  public interface GridCellProvider {
    GridCellInfo info(GridRecord row, GridColumn column);
  }
  public static final class GridEditOptions {
    public boolean enabled, startTyping, allowNull;
    public GridPrepare prepare;
    private GridEditOptions copy() {
      var o = new GridEditOptions();
      o.enabled = enabled;
      o.startTyping = startTyping;
      o.allowNull = allowNull;
      o.prepare = prepare;
      return o;
    }
  }
  public record GridChange(String rowId, String columnId, GridValue value) {}
  public record GridPasteRequest(long id, long revision, List<GridChange> changes) {
    public GridPasteRequest {
      changes = List.copyOf(changes);
    }
  }
  public record GridEvent(String kind, String rowId, String columnId, String text, long id,
      long revision, GridValue value) {
    public GridEvent() {
      this("", "", "", "", 0, 0, null);
    }
    public GridEvent(String kind, String rowId, String columnId) {
      this(kind, rowId, columnId, "", 0, 0, null);
    }
  }
  public static final class GridEditSession {
    public long id, revision;
    public String rowId, columnId, error = "", move = "";
    public GridValue original;
    public Text buffer;
    public boolean isNull, pending;
  }
  public static final class GridViewState {
    public List<GridColumn> columns = new ArrayList<>();
    public Map<String, GridColumnOptions> columnOptions = new HashMap<>();
    public String rowId = "", columnId = "", topRowId = "", leftColumnId = "", sortColumn = "",
                  sortDirection = "", mode = "cell", filter = "";
    public GridRange selection;
  }
  private static int gridNumber(int n, int lo, int hi, String name) {
    if (n < lo || n > hi)
      throw new IllegalArgumentException("invalid " + name);
    return n;
  }
  private static State gridCombine(State a, State b) {
    var s = new State();
    s.disabled = a.disabled || b.disabled;
    s.readOnly = a.readOnly || b.readOnly;
    s.busy = a.busy || b.busy;
    s.selected = a.selected || b.selected;
    s.edited = a.edited || b.edited;
    s.invalid = a.invalid || b.invalid;
    return s;
  }
  private static String gridRaw(GridRecord r, String id) {
    var v = r.cells.get(id);
    return v == null ? "" : v;
  }
  private static String gridFit(String value, int width, String align, boolean ellipsis) {
    var text = clip(value, width, ellipsis);
    int space = Math.max(0, width - cells(text));
    return align.equals("right") ? " ".repeat(space) + text
        : align.equals("center") ? " ".repeat(space / 2) + text + " ".repeat(space - space / 2)
                                 : text + " ".repeat(space);
  }
  public static List<List<String>> parseGridTSV(String text, int maxCells) {
    gridNumber(maxCells, 1, 1000000, "cell limit");
    dialogText(text, 16 * 1024 * 1024);
    var rows = new ArrayList<List<String>>();
    var row = new ArrayList<String>();
    var value = new StringBuilder();
    boolean quoted = false, closed = false, started = false;
    int count = 0;
    for (int i = 0; i < text.length(); i++) {
      char c = text.charAt(i);
      if (quoted) {
        if (c == '"') {
          if (i + 1 < text.length() && text.charAt(i + 1) == '"') {
            value.append('"');
            i++;
            continue;
          }
          quoted = false;
          closed = true;
        } else
          value.append(c);
        continue;
      }
      boolean nl = c == '\n' || c == '\r' && i + 1 < text.length() && text.charAt(i + 1) == '\n';
      if (c == '\t' || nl) {
        if (c == '\t' || !row.isEmpty() || started || closed || !value.isEmpty()) {
          if (++count > maxCells)
            throw new IllegalArgumentException("paste exceeds cell limit");
          row.add(value.toString());
          value.setLength(0);
          closed = started = false;
        }
        if (nl) {
          if (!row.isEmpty()) {
            rows.add(List.copyOf(row));
            row.clear();
          }
          if (c == '\r')
            i++;
        }
      } else if (closed)
        throw new IllegalArgumentException("characters after closing quote");
      else if (c == '"') {
        if (started || !value.isEmpty())
          throw new IllegalArgumentException("quote inside unquoted field");
        quoted = started = true;
      } else {
        value.append(c);
        started = true;
      }
    }
    if (quoted)
      throw new IllegalArgumentException("unterminated quoted field");
    if (!row.isEmpty() || started || closed || !value.isEmpty()) {
      if (++count > maxCells)
        throw new IllegalArgumentException("paste exceeds cell limit");
      row.add(value.toString());
      rows.add(List.copyOf(row));
    }
    if (rows.isEmpty() || rows.stream().anyMatch(r -> r.size() != rows.get(0).size()))
      throw new IllegalArgumentException("empty or ragged paste");
    return List.copyOf(rows);
  }
  public static List<List<String>> parseGridTSV(String text) {
    return parseGridTSV(text, 10000);
  }
  public static String formatGridTSV(List<List<String>> rows) {
    var out = new ArrayList<String>();
    for (var r : rows) {
      var line = new ArrayList<String>();
      for (var s : r)
        line.add(
            s.isEmpty() || s.chars().anyMatch(c -> c == '\t' || c == '\n' || c == '\r' || c == '"')
                ? "\"" + s.replace("\"", "\"\"") + "\""
                : s);
      out.add(String.join("\t", line));
    }
    return String.join("\n", out);
  }
  public static final class Grid {
    private GridSource source;
    public List<GridColumn> columns;
    public int row, column, top, left;
    private GridOptions config = new GridOptions();
    private GridLabels labels = new GridLabels();
    private GridEditOptions editOptions = new GridEditOptions();
    private final Map<String, GridColumnOptions> columnConfig = new HashMap<>();
    private final Map<String, Integer> cellPan = new HashMap<>();
    private GridCellProvider cellProvider;
    public GridEditSession edit;
    public GridRange selected;
    private GridPasteRequest paste;
    private long serial, revision, appliedRevision;
    private boolean callback;
    public boolean caseSensitive, useDisplay;
    public String query = "", sortColumn = "", sortDirection = "";
    public GridDataStatus status = new GridDataStatus();
    private record Hits(int width, int height, GridGeometry geometry, Map<Integer, String> rows,
        List<String> signature) {}
    private Hits hits;
    private GridCapture capture;
    private String paintKey = "";
    private record Current(GridRecord row, GridColumn column) {}
    public Grid(List<GridColumn> columns, List<GridRecord> rows) {
      this(columns, new MemoryRows(rows));
    }
    public Grid(List<GridColumn> columns, GridSource source) {
      if (columns.size() > 65536)
        throw new IllegalArgumentException("too many grid columns");
      this.columns = new ArrayList<>();
      var ids = new HashSet<String>();
      for (var c : columns) {
        if (c.id.isEmpty() || !ids.add(c.id) || !List.of("", "left", "right").contains(c.pin))
          throw new IllegalArgumentException("invalid grid column");
        dialogText(c.id, 1000000);
        dialogText(c.label, 1000000);
        gridNumber(c.width, 1, 4096, "column width");
        this.columns.add(c.copy());
      }
      gridNumber(invoke(() -> source.size()), 0, 1000000000, "row count");
      this.source = source;
    }
    private void mutation() {
      if (callback)
        throw new IllegalArgumentException("grid mutation inside callback");
    }
    private <T> T invoke(java.util.function.Supplier<T> fn) {
      if (callback)
        throw new IllegalArgumentException("recursive grid callback");
      callback = true;
      try {
        return fn.get();
      } finally {
        callback = false;
      }
    }
    private int sourceSize() {
      return gridNumber(invoke(() -> source.size()), 0, 1000000000, "row count");
    }
    private OptionalInt sourceIndex(String id) {
      var i = invoke(() -> source.indexOf(id));
      if (i.isPresent())
        gridNumber(i.getAsInt(), 0, sourceSize() - 1, "source index");
      return i;
    }
    private GridRecord record(int i) {
      gridNumber(i, 0, sourceSize() - 1, "row index");
      var r = invoke(() -> source.row(i).copy());
      if (r.id.isEmpty() || sourceIndex(r.id).orElse(-1) != i)
        throw new IllegalArgumentException("inconsistent grid source IDs");
      return r;
    }
    public List<GridColumn> visibleColumns() {
      var cs = new ArrayList<GridColumn>();
      for (var c : columns)
        if (!c.hidden)
          cs.add(c.copy());
      cs.sort(Comparator.comparingInt(c
          -> c.pin.equals("left")     ? 0
              : c.pin.equals("right") ? 2
                                      : 1));
      return cs;
    }
    private Current current() {
      var cs = visibleColumns();
      int n = sourceSize();
      if (cs.isEmpty() || n == 0)
        return null;
      row = Math.max(0, Math.min(n - 1, row));
      column = Math.max(0, Math.min(cs.size() - 1, column));
      var r = record(row);
      if (r.state.disabled) {
        boolean found = false;
        int scanned = 0;
        for (int i = row + 1; i < n && scanned < 100000; i++, scanned++) {
          r = record(i);
          if (!r.state.disabled) {
            row = i;
            found = true;
            break;
          }
        }
        if (!found)
          for (int i = row - 1; i >= 0 && scanned < 100000; i--, scanned++) {
            r = record(i);
            if (!r.state.disabled) {
              row = i;
              found = true;
              break;
            }
          }
        if (!found)
          return null;
      }
      return new Current(r, cs.get(column));
    }
    private GridCellInfo info(GridRecord r, GridColumn c) {
      var i = cellProvider == null ? new GridCellInfo()
                                   : invoke(() -> cellProvider.info(r.copy(), c.copy())).copy();
      i.state =
          gridCombine(gridCombine(i.state, r.state), r.cellStates.getOrDefault(c.id, new State()));
      i.isNull = i.isNull || r.cells.containsKey(c.id) && r.cells.get(c.id) == null;
      return i;
    }
    private GridValue prepared(GridRecord r, GridColumn c) {
      var v = editOptions.prepare == null
          ? new GridValue(gridRaw(r, c.id), info(r, c).isNull)
          : invoke(() -> editOptions.prepare.prepare(r.copy(), c.copy()));
      if (v != null)
        dialogText(v.text(), 16 * 1024 * 1024);
      return v;
    }
    private boolean editable(GridRecord r, GridColumn c) {
      return !config.disableEditing && !c.hidden && c.editable && info(r, c).state.editable()
          && prepared(r, c) != null;
    }
    private void invalidate() {
      mutation();
      revision++;
      edit = null;
      paste = null;
      hits = null;
      capture = null;
    }
    public String rowId() {
      var p = current();
      return p == null ? "" : p.row.id;
    }
    public String columnId() {
      var p = current();
      return p == null ? "" : p.column.id;
    }
    public long revision() {
      return revision;
    }
    public GridLabels labels() {
      return labels.copy();
    }
    public void setLabels(GridLabels value) {
      mutation();
      var v = value.copy();
      for (var text : List.of(v.nullText, v.loading, v.empty, v.range, v.more))
        dialogText(text, 1000000);
      labels = v;
    }
    public GridOptions options() {
      return config.copy();
    }
    public GridPasteRequest pendingPaste() {
      return paste;
    }
    public void setRows(List<GridRecord> rows) {
      setSource(new MemoryRows(rows));
    }
    private record PreparedSource(GridSource source, int row, GridRange selected) {}
    private PreparedSource prepareSource(GridSource source) {
      mutation();
      String id = rowId();
      GridRange range = selected;
      return invoke(() -> {
        var probe = new Grid(columns, source);
        int at = probe.sourceIndex(id).orElse(-1);
        if (at >= 0 && !probe.record(at).id.equals(id))
          throw new IllegalArgumentException("inconsistent grid source IDs");
        boolean valid = true;
        if (range != null) {
          var cs = probe.visibleColumns();
          for (var pair : List.of(List.of(range.anchorRow(), range.anchorColumn()),
                   List.of(range.endRow(), range.endColumn()))) {
            int i = probe.sourceIndex(pair.get(0)).orElse(-1);
            if (i < 0 || cs.stream().noneMatch(c -> c.id.equals(pair.get(1))))
              valid = false;
            else if (!probe.record(i).id.equals(pair.get(0)))
              throw new IllegalArgumentException("inconsistent grid source IDs");
          }
        }
        return new PreparedSource(source, Math.max(0, at), valid ? range : null);
      });
    }
    private void installSource(PreparedSource p) {
      source = p.source();
      row = p.row();
      selected = p.selected();
      invalidate();
    }
    public void setSource(GridSource source) {
      installSource(prepareSource(source));
    }
    public boolean focus(String rowId, String columnId) {
      mutation();
      int i = sourceIndex(rowId).orElse(-1), j = -1;
      var cs = visibleColumns();
      for (int k = 0; k < cs.size(); k++)
        if (cs.get(k).id.equals(columnId))
          j = k;
      if (i < 0 || i >= sourceSize() || j < 0)
        return false;
      var r = record(i);
      if (!r.id.equals(rowId) || r.state.disabled)
        return false;
      if (edit != null && (!edit.rowId.equals(rowId) || !edit.columnId.equals(columnId)))
        edit = null;
      row = i;
      column = j;
      return true;
    }
    public void setOptions(GridOptions options) {
      var o = options.copy();
      gridNumber(o.padding, 0, 8, "padding");
      gridNumber(o.rowSpacing, 0, 4, "row spacing");
      gridNumber(o.gutterWidth, 0, 128, "gutter width");
      gridNumber(o.maxCopyCells, 1, 1000000, "copy limit");
      var allowed = Set.of(
          "position", "column", "selection", "sort", "filter", "loading", "more", "meta", "error");
      if (!List.of("cell", "row", "range").contains(o.selection)
          || new HashSet<>(o.statusFields).size() != o.statusFields.size()
          || !allowed.containsAll(o.statusFields))
        throw new IllegalArgumentException("invalid grid options");
      invalidate();
      config = o;
    }
    public void setEditOptions(GridEditOptions options) {
      invalidate();
      editOptions = options.copy();
    }
    public void setCellInfo(GridCellProvider fn) {
      invalidate();
      cellProvider = fn;
    }
    public void setColumnOptions(String id, GridColumnOptions options) {
      var c = columns.stream()
                  .filter(x -> x.id.equals(id))
                  .findFirst()
                  .orElseThrow(() -> new IllegalArgumentException("unknown column"));
      var o = options.copy();
      gridNumber(o.minWidth, 1, 4096, "minimum width");
      gridNumber(o.maxWidth, o.minWidth, 4096, "maximum width");
      gridNumber(o.expand, 0, 4096, "expansion");
      if (!List.of("left", "right", "center", "auto").contains(o.align)
          || !List.of("clip", "ellipsis", "scroll").contains(o.overflow))
        throw new IllegalArgumentException("invalid column options");
      invalidate();
      columnConfig.put(id, o);
      c.width = Math.max(o.minWidth, Math.min(o.maxWidth, c.width));
    }
    public void setColumnLayout(List<GridColumn> layout) {
      if (layout.size() != columns.size())
        throw new IllegalArgumentException("incompatible column layout");
      var next = new ArrayList<GridColumn>();
      var ids = new HashSet<String>();
      for (var item : layout) {
        var c = columns.stream()
                    .filter(x -> x.id.equals(item.id))
                    .findFirst()
                    .orElseThrow(() -> new IllegalArgumentException("unknown column"))
                    .copy();
        if (!ids.add(c.id) || !List.of("", "left", "right").contains(item.pin))
          throw new IllegalArgumentException("invalid column layout");
        c.hidden = item.hidden;
        c.pin = item.pin;
        next.add(c);
      }
      var p = current();
      invalidate();
      columns = next;
      if (p != null)
        focus(p.row.id, p.column.id);
    }
    private boolean workValid(String rid, String cid, long revision) {
      if (revision != this.revision)
        return false;
      int i = sourceIndex(rid).orElse(-1);
      var c = visibleColumns().stream().filter(x -> x.id.equals(cid)).findFirst().orElse(null);
      if (i < 0 || i >= sourceSize() || c == null)
        return false;
      var r = record(i);
      return r.id.equals(rid) && editable(r, c);
    }
    public boolean beginEdit() {
      return beginEdit(null);
    }
    public boolean beginEdit(String first) {
      mutation();
      var p = current();
      if (p == null || edit != null || paste != null || !editOptions.enabled
          || !editable(p.row, p.column))
        return false;
      var v = prepared(p.row, p.column);
      if (v == null)
        return false;
      var e = new GridEditSession();
      e.id = ++serial;
      e.revision = revision;
      e.rowId = p.row.id;
      e.columnId = p.column.id;
      e.original = v;
      e.isNull = first == null && v.isNull();
      e.buffer = new Text(first == null ? v.text() : first);
      e.buffer.multiline = false;
      edit = e;
      hits = null;
      return true;
    }
    public boolean resolveEdit(long id, String error, GridSource source) {
      mutation();
      var e = edit;
      if (e == null || !e.pending || e.id != id || e.revision != revision)
        return false;
      if (!workValid(e.rowId, e.columnId, e.revision)) {
        edit = null;
        return false;
      }
      if (!error.isEmpty()) {
        e.pending = false;
        e.error = error;
        return true;
      }
      var prepared = source == null ? null : prepareSource(source);
      edit = null;
      if (prepared != null)
        installSource(prepared);
      focus(e.rowId, e.columnId);
      if (!e.move.isEmpty() && moveEditable(e.move.equals("previous")))
        beginEdit();
      return true;
    }
    public boolean resolveEdit(long id) {
      return resolveEdit(id, "", null);
    }
    public boolean resolveEdit(long id, String error) {
      return resolveEdit(id, error, null);
    }
    private boolean moveEditable(boolean previous) {
      var cs = visibleColumns();
      if (cs.isEmpty())
        return false;
      long step = previous ? -1 : 1, start = (long) row * cs.size() + column,
           n = (long) sourceSize() * cs.size();
      for (long at = start + step, scanned = 0; at >= 0 && at < n && scanned < 100000;
          at += step, scanned++) {
        int i = (int) (at / cs.size()), j = (int) (at % cs.size());
        var r = record(i);
        if (editable(r, cs.get(j)))
          return focus(r.id, cs.get(j).id);
      }
      return false;
    }
    public GridEvent handle(String action) {
      return handle(action, 10, "");
    }
    public GridEvent handle(String action, int height, String text) {
      mutation();
      gridNumber(height, 0, 4096, "height");
      if (config.disableKeyboard)
        return new GridEvent();
      capture = null;
      if (edit == null && List.of("select_up", "select_down", "select_left",
                                  "select_right", "select_home", "select_end",
                                  "select_page_up", "select_page_down")
                              .contains(action))
        return extendNavigation(action.substring(7), height);
      var e = edit;
      if (e != null) {
        if (action.equals("cancel")) {
          edit = null;
          return new GridEvent("edit_cancel", e.rowId, e.columnId);
        }
        if (!workValid(e.rowId, e.columnId, e.revision)) {
          edit = null;
          return new GridEvent("edit_stale", "", "");
        }
        if (e.pending)
          return new GridEvent();
        if (action.equals("null")) {
          if (!editOptions.allowNull)
            return new GridEvent();
          e.isNull = !e.isNull;
          e.error = "";
        } else if (List.of("submit", "activate", "next", "previous").contains(action)) {
          e.id = ++serial;
          e.pending = true;
          e.error = "";
          e.move = List.of("next", "previous").contains(action) ? action : "";
          return new GridEvent("edit_submit", e.rowId, e.columnId, "", e.id, e.revision,
              new GridValue(e.buffer.value(), e.isNull));
        } else {
          if (List.of("insert", "paste", "backspace", "delete").contains(action)) {
            e.isNull = false;
            e.error = "";
          }
          var out = e.isNull ? new Event() : e.buffer.handle(action, text);
          if (List.of("copy", "cut").contains(out.kind()))
            return new GridEvent(out.kind(), e.rowId, e.columnId, out.text(), 0, 0, null);
        }
        return new GridEvent("edit_change", e.rowId, e.columnId);
      }
      var p = current();
      if (p == null)
        return new GridEvent();
      if (List.of("activate", "edit").contains(action))
        return new GridEvent(beginEdit() ? "edit_begin" : "edit_denied", p.row.id, p.column.id);
      if (action.equals("insert") && !text.isEmpty() && editOptions.startTyping)
        return new GridEvent(beginEdit(text) ? "edit_begin" : "edit_denied", p.row.id, p.column.id);
      if (action.equals("copy"))
        return copySelection(false, "NULL");
      if (action.equals("details"))
        return info(p.row, p.column).state.disabled
            ? new GridEvent()
            : new GridEvent(
                  "details", p.row.id, p.column.id, gridRaw(p.row, p.column.id), 0, 0, null);
      if (List.of("sort", "filter", "search", "page_next", "page_previous").contains(action))
        return request(action.startsWith("page_") ? action.substring(5) : action, text);
      int target = switch (action) {
        case "up" -> row - 1;
        case "down" -> row + 1;
        case "home" -> 0;
        case "end" -> sourceSize() - 1;
        case "page_up" -> row - Math.max(1, height - 1);
        case "page_down" -> row + Math.max(1, height - 1);
        default -> -1;
      };
      if (List.of("up", "down", "home", "end", "page_up", "page_down").contains(action)) {
        int direction = List.of("up", "home", "page_up").contains(action) ? -1 : 1;
        target = Math.max(0, Math.min(sourceSize() - 1, target));
        while (target >= 0 && target < sourceSize()) {
          if (!record(target).state.disabled) {
            row = target;
            break;
          }
          target += direction;
        }
      } else if (List.of("left", "right").contains(action))
        column = Math.max(
            0, Math.min(visibleColumns().size() - 1, column + (action.equals("left") ? -1 : 1)));
      else if (!action.equals("select"))
        return new GridEvent();
      p = current();
      return p == null ? new GridEvent() : new GridEvent("select", p.row.id, p.column.id);
    }
    public Optional<GridPasteRequest> requestPaste(String text) {
      return requestPaste(text, 10000, null);
    }
    public Optional<GridPasteRequest> requestPaste(String text, int maxCells, String nullText) {
      mutation();
      if (edit != null || paste != null)
        return Optional.empty();
      List<List<String>> values;
      try {
        values = parseGridTSV(text, maxCells);
      } catch (IllegalArgumentException e) {
        return Optional.empty();
      }
      var cs = visibleColumns();
      if (cs.isEmpty() || (long) row + values.size() > sourceSize()
          || (long) column + values.get(0).size() > cs.size())
        return Optional.empty();
      var changes = new ArrayList<GridChange>();
      for (int dy = 0; dy < values.size(); dy++) {
        var r = record(row + dy);
        for (int dx = 0; dx < values.get(dy).size(); dx++) {
          var c = cs.get(column + dx);
          String v = values.get(dy).get(dx);
          if (!editable(r, c))
            return Optional.empty();
          changes.add(
              new GridChange(r.id, c.id, new GridValue(v, nullText != null && v.equals(nullText))));
        }
      }
      paste = new GridPasteRequest(++serial, revision, changes);
      return Optional.of(paste);
    }
    public boolean resolvePaste(long id, GridSource source) {
      mutation();
      if (paste == null || paste.id() != id || paste.revision() != revision)
        return false;
      for (var c : paste.changes())
        if (!workValid(c.rowId(), c.columnId(), paste.revision())) {
          paste = null;
          return false;
        }
      var prepared = source == null ? null : prepareSource(source);
      paste = null;
      if (prepared != null)
        installSource(prepared);
      return true;
    }
    public boolean resolvePaste(long id) {
      return resolvePaste(id, null);
    }
    public void cancelPaste() {
      mutation();
      paste = null;
    }
    public boolean find(String query, boolean previous, int maxCells) {
      mutation();
      gridNumber(maxCells, 1, 1000000, "find limit");
      var cs = visibleColumns();
      long total = (long) sourceSize() * cs.size();
      if (query.isEmpty() || total == 0 || edit != null || paste != null)
        return false;
      this.query = query;
      String needle = caseSensitive ? query : fold(query);
      long start = (long) row * cs.size() + column;
      for (long step = 1; step <= Math.min(total, maxCells); step++) {
        long at = (start + (previous ? -step : step) + total) % total;
        int i = (int) (at / cs.size()), j = (int) (at % cs.size());
        var r = record(i);
        var c = cs.get(j);
        var info = info(r, c);
        if (info.state.disabled)
          continue;
        String value = useDisplay && info.hasDisplay ? info.display
            : useDisplay && info.isNull              ? labels.nullText
                                                     : gridRaw(r, c.id);
        if ((caseSensitive ? value : fold(value)).contains(needle)) {
          row = i;
          column = j;
          return true;
        }
      }
      return false;
    }
    public boolean find(String query) {
      return find(query, false, 100000);
    }
    public GridEvent request(String kind, String text) {
      mutation();
      if (!List.of("sort", "filter", "search", "next", "previous").contains(kind))
        throw new IllegalArgumentException("unknown grid request");
      if (kind.equals("sort") && config.disableHeaderSort)
        return new GridEvent();
      var p = current();
      invalidate();
      return new GridEvent(kind + "_request", p == null ? "" : p.row.id,
          p == null ? "" : p.column.id, text, 0, revision, null);
    }
    public boolean applySource(long revision, GridSource source) {
      if (revision != this.revision || revision <= appliedRevision)
        return false;
      setSource(source);
      appliedRevision = revision;
      return true;
    }
    public void setSelection(GridRange selection) {
      mutation();
      if (selection == null) {
        selected = null;
        return;
      }
      var cs = visibleColumns();
      for (var pair : List.of(List.of(selection.anchorRow(), selection.anchorColumn()),
               List.of(selection.endRow(), selection.endColumn()))) {
        int i = sourceIndex(pair.get(0)).orElse(-1);
        if (i < 0 || i >= sourceSize() || !record(i).id.equals(pair.get(0))
            || cs.stream().noneMatch(c -> c.id.equals(pair.get(1))))
          throw new IllegalArgumentException("unknown range ID");
      }
      selected = selection;
    }
    private int[] selectionBounds() {
      var cs = visibleColumns();
      if (cs.isEmpty() || sourceSize() == 0)
        return null;
      if (selected == null)
        return new int[] {row, config.selection.equals("row") ? 0 : column, row,
            config.selection.equals("row") ? cs.size() - 1 : column};
      int a = sourceIndex(selected.anchorRow()).orElse(-1),
          b = sourceIndex(selected.endRow()).orElse(-1), c = -1, d = -1;
      for (int i = 0; i < cs.size(); i++) {
        if (cs.get(i).id.equals(selected.anchorColumn()))
          c = i;
        if (cs.get(i).id.equals(selected.endColumn()))
          d = i;
      }
      if (a < 0 || b < 0 || c < 0 || d < 0)
        return null;
      return new int[] {Math.min(a, b), Math.min(c, d), Math.max(a, b), Math.max(c, d)};
    }
    public GridEvent copySelection() {
      return copySelection(false, "NULL");
    }
    public GridEvent copySelection(boolean display, String nullText) {
      if (config.disableCopy)
        return new GridEvent();
      var bounds = selectionBounds();
      if (bounds == null)
        return new GridEvent();
      int a = bounds[0], b = bounds[1], c = bounds[2], d = bounds[3];
      var cs = visibleColumns();
      if (a < 0 || b < 0 || c >= sourceSize() || d >= cs.size()
          || (long) (c - a + 1) * (d - b + 1) > config.maxCopyCells)
        return new GridEvent("copy_rejected", "", "");
      var values = new ArrayList<List<String>>();
      long bytes = 0;
      for (int i = a; i <= c; i++) {
        var r = record(i);
        var line = new ArrayList<String>();
        for (int j = b; j <= d; j++) {
          var col = cs.get(j);
          var info = info(r, col);
          if (info.state.disabled)
            return new GridEvent("copy_rejected", "", "");
          String value = display && info.hasDisplay ? info.display
              : info.isNull                         ? nullText
                                                    : gridRaw(r, col.id);
          bytes += value.getBytes(java.nio.charset.StandardCharsets.UTF_8).length;
          if (bytes > 16 * 1024 * 1024)
            return new GridEvent("copy_rejected", "", "");
          line.add(value);
        }
        values.add(line);
      }
      return new GridEvent("copy", "", "", formatGridTSV(values), 0, 0, null);
    }
    public boolean resizeColumn(String id, int width) {
      if (config.disableResize)
        return false;
      var c = columns.stream().filter(x -> x.id.equals(id)).findFirst().orElse(null);
      if (c == null)
        return false;
      gridNumber(width, 1, 4096, "column width");
      var o = columnConfig.getOrDefault(id, new GridColumnOptions());
      invalidate();
      c.width = Math.max(o.minWidth, Math.min(o.maxWidth, width));
      return true;
    }
    public boolean autoFitColumn(String id, int height) {
      gridNumber(height, 0, 4096, "height");
      var c = columns.stream().filter(x -> x.id.equals(id)).findFirst().orElse(null);
      if (c == null || config.disableResize)
        return false;
      int w = cells(c.label.isEmpty() ? c.id : c.label);
      for (int i = top; i < Math.min(sourceSize(), top + height); i++) {
        var r = record(i);
        var info = info(r, c);
        w = Math.max(w,
            cells(info.hasDisplay ? info.display
                    : info.isNull ? labels.nullText
                                  : gridRaw(r, id))
                + (info.state.edited && config.showCellMarkers ? 2 : 0));
      }
      return resizeColumn(id, Math.max(1, Math.min(4096, w + 2 * config.padding)));
    }
    public void panCell(String id, int offset) {
      mutation();
      gridNumber(offset, 0, 1000000, "cell pan");
      if (columns.stream().noneMatch(c -> c.id.equals(id)))
        throw new IllegalArgumentException("unknown column");
      cellPan.put(id, offset);
    }
    public GridGeometry geometry(int width, int height) {
      gridNumber(width, 0, 65535, "width");
      gridNumber(height, 0, 4096, "height");
      gridNumber(top, 0, 1000000000, "top row");
      gridNumber(left, 0, 1000000, "left column");
      int header = !config.hideHeader && height > 0 ? 1 : 0,
          footer = config.statusBar && height > header ? 1 : 0,
          stride = 1 + config.rowSpacing + (config.horizontalLines ? 1 : 0),
          body = (Math.max(0, height - header - footer) + stride - 1) / stride;
      var p = current();
      if (p != null && body > 0) {
        top = Math.min(top, row);
        if (row >= top + body)
          top = row - body + 1;
      }
      int gutter = Math.min(width,
              Math.max(config.gutterWidth,
                  config.rowNumbers ? String.valueOf(Math.max(1, sourceSize())).length() + 1 : 0)),
          sep = config.verticalLines ? 1 : 0;
      var cs = visibleColumns();
      var automatic =
          cs.stream()
              .filter(c -> columnConfig.containsKey(c.id) && columnConfig.get(c.id).autoFit)
              .toList();
      if (!automatic.isEmpty()) {
        var records = new ArrayList<GridRecord>();
        for (int i = top; i < Math.min(sourceSize(), top + Math.min(body, 256)); i++)
          records.add(record(i));
        int sampled = 0;
        for (var c : automatic) {
          var co = columnConfig.get(c.id);
          int w = cells(c.label.isEmpty() ? c.id : c.label) + 2 * config.padding;
          for (var r : records) {
            if (sampled >= 100000)
              break;
            sampled++;
            var info = info(r, c);
            String value = info.hasDisplay ? info.display
                : info.isNull              ? labels.nullText
                                           : gridRaw(r, c.id);
            w = Math.max(w,
                cells(value) + 2 * config.padding
                    + (info.state.edited && config.showCellMarkers ? 2 : 0));
          }
          c.width = Math.max(co.minWidth, Math.min(co.maxWidth, w));
        }
      }

      var pinsLeft = new ArrayList<GridColumn>();
      var pinsRight = new ArrayList<GridColumn>();
      var normal = new ArrayList<GridColumn>();
      for (var c : cs)
        (c.pin.equals("left") ? pinsLeft : c.pin.equals("right") ? pinsRight : normal).add(c);
      left = Math.min(left, Math.max(0, normal.size() - 1));
      int rightWidth = pinsRight.stream().mapToInt(c -> c.width + sep).sum();
      if (p != null) {
        int at = -1;
        for (int i = 0; i < normal.size(); i++)
          if (normal.get(i).id.equals(p.column.id))
            at = i;
        if (at >= 0) {
          left = Math.min(left, at);
          int capacity = Math.max(0,
              width - gutter - rightWidth - pinsLeft.stream().mapToInt(c -> c.width + sep).sum());
          while (left < at) {
            int need = 0;
            for (int i = left; i <= at; i++) need += normal.get(i).width + sep;
            if (need <= capacity)
              break;
            left++;
          }
        }
      }
      int end = width - Math.min(Math.max(0, width - gutter), rightWidth), x = gutter;
      var spans = new ArrayList<GridSpan>();
      var scrolling = new ArrayList<>(pinsLeft);
      scrolling.addAll(normal.subList(left, normal.size()));
      for (var c : scrolling) {
        int w = Math.min(c.width, Math.max(0, end - x));
        if (w > 0)
          spans.add(new GridSpan(c.id, x, w));
        x += w + sep;
        if (x >= end)
          break;
      }
      x = Math.max(gutter, end);
      for (var c : pinsRight) {
        int w = Math.min(c.width, Math.max(0, width - x));
        if (w > 0)
          spans.add(new GridSpan(c.id, x, w));
        x += w + sep;
        if (x >= width)
          break;
      }
      int used = gutter, total = 0;
      for (var s : spans)
        if (s.x() < end) {
          used = Math.max(used, s.x() + s.width() + sep);
          total += columnConfig.getOrDefault(s.id(), new GridColumnOptions()).expand;
        }
      int room = Math.max(0, end - used), remaining = room, shift = 0;
      if (room > 0 && total > 0)
        for (int i = 0; i < spans.size(); i++) {
          var s = spans.get(i);
          if (s.x() >= end)
            continue;
          var co = columnConfig.getOrDefault(s.id(), new GridColumnOptions());
          int extra =
              Math.min(remaining, Math.min(co.maxWidth - s.width(), room * co.expand / total));
          spans.set(i, new GridSpan(s.id(), s.x() + shift, s.width() + extra));
          shift += extra;
          remaining -= extra;
        }
      return new GridGeometry(top, left, gutter, header, footer, body, stride, spans);
    }
    private record EditorWindow(String text, int x, int glyph, int start) {}
    private EditorWindow editorWindow(String value, int cursor, int width) {
      var gs = graphemes(value);
      int at = Math.max(0, Math.min(gs.size(), cursor)), start = at, x = 0,
          reserve = Math.min(width, Math.max(1, at < gs.size() ? cells(clean(gs.get(at))) : 1));
      while (start > 0) {
        int w = cells(clean(gs.get(start - 1)));
        if (x + w > width - reserve)
          break;
        start--;
        x += w;
      }
      var text = new StringBuilder();
      int used = 0;
      for (int i = start; i < gs.size(); i++) {
        String g = clean(gs.get(i));
        int w = cells(g);
        if (used + w > width)
          break;
        text.append(g);
        used += w;
      }
      int glyph = Math.max(1, at < gs.size() ? cells(clean(gs.get(at))) : 1);
      return new EditorWindow(text.toString(), x, glyph > width ? 1 : glyph,
                              start);
    }
    public Optional<int[]> editCursor(int width, int height) {
      var e = edit;
      if (e == null || e.pending || e.isNull || !workValid(e.rowId, e.columnId, e.revision))
        return Optional.empty();
      var geo = geometry(width, height);
      int i = sourceIndex(e.rowId).orElse(-1);
      var span =
          geo.columns().stream().filter(s -> s.id().equals(e.columnId)).findFirst().orElse(null);
      if (i < geo.top() || i >= geo.top() + geo.bodyRows() || span == null)
        return Optional.empty();
      var col = columns.stream().filter(c -> c.id.equals(span.id())).findFirst().orElseThrow();
      var info = info(record(i), col);
      int extra = info.state.edited && config.showCellMarkers ? 2 : 0,
          room = span.width() - 2 * config.padding - extra,
          y = geo.headerRows() + (i - geo.top()) * geo.stride();
      if (room <= 0 || y >= height - geo.footerRows())
        return Optional.empty();
      var window = editorWindow(e.buffer.value(), e.buffer.cursor, room);
      return Optional.of(
          new int[] {span.x() + config.padding + extra + window.x(), y, window.glyph()});
    }
    public Optional<TextDocument> details() {
      var p = current();
      return p == null || info(p.row, p.column).state.disabled
          ? Optional.empty()
          : Optional.of(TextDocument.viewer(gridRaw(p.row, p.column.id)));
    }
    public String statusText() {
      var p = current();
      gridNumber(status.totalRows, 0, 1000000000, "total rows");
      var f = new HashMap<String, String>();
      f.put("position",
          (p == null ? 0 : row + 1) + "/"
              + (status.totalRows == 0 ? sourceSize() : status.totalRows));
      f.put("column", p == null ? "" : p.column.label.isEmpty() ? p.column.id : p.column.label);
      f.put("selection", selected == null ? "" : labels.range);
      f.put("sort", (sortColumn + " " + sortDirection).strip());
      f.put("filter", status.filter);
      f.put("loading", status.loading ? labels.loading : "");
      f.put("more", status.hasMore ? labels.more : "");
      f.put("meta", status.metadata);
      f.put("error", edit != null && !edit.error.isEmpty() ? edit.error : status.error);
      if (!f.get("error").isEmpty())
        return f.get("error");
      var parts = new ArrayList<String>();
      for (var key : config.statusFields)
        if (!f.get(key).isEmpty())
          parts.add(f.get(key));
      return String.join(" | ", parts);
    }
    private List<String> columnSignature() {
      var out = new ArrayList<String>();
      for (var c : columns) {
        out.add(c.id);
        out.add(String.valueOf(c.width));
        out.add(c.pin);
        out.add(String.valueOf(c.hidden));
        out.add(String.valueOf(c.editable));
      }
      return out;
    }
    public void draw(Canvas canvas, Rect r) {
      draw(canvas, r, true, false);
    }
    public void draw(Canvas canvas, Rect r, boolean focused, boolean ascii) {
      gridNumber(r.x(), 0, 1000000000, "x");
      gridNumber(r.y(), 0, 1000000000, "y");
      var geo = geometry(r.width(), r.height());
      var hitRows = new HashMap<Integer, String>();
      var signature = columnSignature();
      var o = config;
      var child = new Canvas(
          r.width(), r.height(), canvas.palette, o.useSurface ? "surface" : canvas.surfaceRole);
      String currentId = columnId(), sep = ascii || o.ascii ? "|" : "│",
             horizontal = ascii || o.ascii ? "-" : "─";
      var byId = new HashMap<String, GridColumn>();
      for (var c : columns) byId.put(c.id, c);
      var bounds = selectionBounds();
      var visible = visibleColumns();
      if (geo.headerRows() > 0) {
        child.fill(new Rect(0, 0, r.width(), 1), "grid.header");
        for (var span : geo.columns()) {
          var c = byId.get(span.id());
          String title = c.label.isEmpty() ? c.id : c.label;
          if (sortColumn.equals(c.id))
            title += sortDirection.equals("desc") ? " v" : " ^";
          child.write(span.x(), 0, gridFit(title, span.width(), "left", true),
                      "grid.header", false, span.width());
        }
      }
      for (int dy = 0; dy < geo.bodyRows(); dy++) {
        int i = geo.top() + dy, y = geo.headerRows() + dy * geo.stride();
        if (y >= r.height() - geo.footerRows() || i >= sourceSize())
          break;
        var record = record(i);
        hitRows.put(i, record.id);
        if (geo.gutter() > 0)
          child.write(0, y,
              gridFit(o.rowNumbers ? String.valueOf(i + 1) : "", Math.max(0, geo.gutter() - 1),
                  "right", false)
                  + " ",
              record.state.disabled ? "disabled" : "hint", false, geo.gutter());
        for (var span : geo.columns()) {
          var c = byId.get(span.id());
          var info = info(record, c);
          var state = info.state;
          boolean active = i == row && c.id.equals(currentId);
          int j = 0;
          while (j < visible.size() && !visible.get(j).id.equals(c.id)) j++;
          boolean inRange = bounds != null && bounds[0] <= i && i <= bounds[2] && bounds[1] <= j
              && j <= bounds[3],
                  editing = edit != null && record.id.equals(edit.rowId)
              && c.id.equals(edit.columnId) && workValid(edit.rowId, edit.columnId, edit.revision);
          String role =
              state.disabled                     ? "disabled"
              : state.invalid                    ? "error"
              : active && o.highlightCell        ? "grid.active"
              : state.edited && o.preserveEdited ? "edited"
              : o.highlightRow && i == row || inRange && selected != null
                  ? "grid.range"
              : o.striped && i % 2 == 1 ? "surface"
                                        : "body";
          if (editing)
            role = edit.pending ? "hint" : !edit.error.isEmpty() ? "error" : "field";
          int pad = Math.min(o.padding, span.width() / 2);
          String marker =
              state.edited && (o.showCellMarkers || role.equals("grid.active"))
                  ? "* "
                  : "";
          int room = Math.max(0, span.width() - 2 * pad - marker.length());
          String text;
          if (editing)
            text = edit.isNull ? labels.nullText
                               : editorWindow(edit.buffer.value(), edit.buffer.cursor, room).text();
          else {
            String value = info.hasDisplay ? info.display
                : info.isNull              ? labels.nullText
                                           : gridRaw(record, c.id);
            var co = columnConfig.getOrDefault(c.id, new GridColumnOptions());
            if (co.overflow.equals("scroll")) {
              int offset = cellPan.getOrDefault(c.id, 0), used = 0;
              var out = new StringBuilder();
              for (var g : graphemes(value)) {
                int n = cells(g);
                if (used >= offset)
                  out.append(g);
                else if (used + n > offset)
                  out.append(" ".repeat(used + n - offset));
                used += n;
              }
              value = out.toString();
            }
            text =
                gridFit(value, room, co.align.equals("auto") && info.numeric ? "right" : co.align,
                    !co.overflow.equals("clip"));
          }
          String value = " ".repeat(pad) + marker + text;
          value += " ".repeat(Math.max(0, span.width() - cells(value)));
          child.write(span.x(), y, value, role, false, span.width());
          if (editing && edit != null && !edit.pending && !edit.isNull) {
            var buf = edit.buffer;
            int lo = Math.min(buf.anchor, buf.cursor),
                hi = Math.max(buf.anchor, buf.cursor);
            if (lo < hi) {
              int start = editorWindow(buf.value(), buf.cursor, room).start(),
                  x = 0;
              var gs = graphemes(buf.value());
              for (int index = start; index < gs.size(); index++) {
                String glyph = clean(gs.get(index));
                int w = cells(glyph);
                if (x + w > room)
                  break;
                if (lo <= index && index < hi)
                  child.write(span.x() + pad + marker.length() + x, y, glyph,
                              "selection", false, w);
                x += w;
              }
            }
          }
        }
        if (o.horizontalLines) {
          int yy = y + 1 + o.rowSpacing;
          if (yy < r.height() - geo.footerRows())
            child.write(geo.gutter(), yy, horizontal.repeat(Math.max(0, r.width() - geo.gutter())),
                "hint", false, r.width() - geo.gutter());
        }
      }
      if (sourceSize() == 0 && geo.headerRows() < r.height() - geo.footerRows())
        child.write(geo.gutter(), geo.headerRows(),
            clip(!status.error.isEmpty() ? status.error
                    : status.loading     ? labels.loading
                                         : labels.empty,
                Math.max(0, r.width() - geo.gutter()), false),
            !status.error.isEmpty() ? "error" : "hint", false, r.width() - geo.gutter());
      if (o.verticalLines)
        for (var span : geo.columns()) {
          int x = span.x() + span.width();
          if (x < r.width())
            for (int y = 0; y < r.height() - geo.footerRows(); y++)
              child.write(x, y, sep,
                          y < geo.headerRows() ? "grid.header" : "hint", false,
                          1);
        }
      if (geo.footerRows() > 0)
        child.write(0, r.height() - 1, clip(statusText(), r.width(), true),
            !status.error.isEmpty() || edit != null && !edit.error.isEmpty() ? "error" : "hint",
            false, r.width());
      if (focused) {
        var cursor = editCursor(r.width(), r.height());
        if (cursor.isPresent()) {
          int[] c = cursor.get();
          child.setCursor(c[0], c[1], c[2]);
        }
      }
      canvas.blit(child, new Rect(0, 0, r.width(), r.height()), r.x(), r.y());
      String key = r.x() + "|" + r.y() + "|" + r.width() + "|" + r.height() +
                   "|" + canvas.palette.theme + "|" + canvas.palette.profile +
                   "|" + canvas.surfaceRole + "|" + ascii + "|" + focused;
      if (!focused || !paintKey.isEmpty() && !paintKey.equals(key))
        capture = null;
      paintKey = key;
      hits = new Hits(r.width(), r.height(), geo, Map.copyOf(hitRows), List.copyOf(signature));
    }
    public GridEvent click(int x, int y, int width, int height) {
      mutation();
      if (config.disableMouse || edit != null || paste != null || hits == null
          || hits.width() != width || hits.height() != height
          || !hits.signature().equals(columnSignature()) || x < 0 || x >= width || y < 0
          || y >= height)
        return new GridEvent();
      var geo = hits.geometry();
      var span = geo.columns()
                     .stream()
                     .filter(s -> s.x() <= x && x < s.x() + s.width())
                     .findFirst()
                     .orElse(null);
      if (span == null)
        return new GridEvent();
      if (y < geo.headerRows()) {
        if (config.disableHeaderSort)
          return new GridEvent();
        var cs = visibleColumns();
        for (int i = 0; i < cs.size(); i++)
          if (cs.get(i).id.equals(span.id()))
            column = i;
        return request("sort", "");
      }
      int dy = y - geo.headerRows();
      if (dy % geo.stride() != 0 || y >= height - geo.footerRows())
        return new GridEvent();
      int i = geo.top() + dy / geo.stride();
      if (i >= sourceSize())
        return new GridEvent();
      var r = record(i);
      if (!r.id.equals(hits.rows().get(i)))
        return new GridEvent();
      var c = columns.stream().filter(v -> v.id.equals(span.id())).findFirst().orElseThrow();
      if (info(r, c).state.disabled || !focus(r.id, c.id))
        return new GridEvent();
      return new GridEvent("select", r.id, c.id);
    }
    private static final class GridCapture {
      String kind, column = "", anchorRow = "", anchorColumn = "";
      int width, height, startX, startWidth, anchorIndex = -1;
      long revision, editId;
      List<String> signature;
      boolean moved, whole;
      GridCapture(String kind) { this.kind = kind; }
    }
    private void armGrid(GridCapture c, int width, int height) {
      c.width = width;
      c.height = height;
      c.revision = revision;
      c.signature = columnSignature();
      capture = c;
    }
    private String[] rangeAnchor(Current p) {
      return selected != null && selectionBounds() != null
          ? new String[] {selected.anchorRow(), selected.anchorColumn()}
          : new String[] {p.row.id, p.column.id};
    }
    private GridEvent extendNavigation(String action, int height) {
      var before = current();
      if (before == null)
        return new GridEvent();
      String[] anchor = rangeAnchor(before);
      int oldRow = row, oldColumn = column;
      var result = handle(action, height, "");
      var after = current();
      if (!result.kind().equals("select") || after == null)
        return result;
      if (info(after.row, after.column).state.disabled) {
        row = oldRow;
        column = oldColumn;
        return new GridEvent();
      }
      setSelection(
          new GridRange(anchor[0], anchor[1], after.row.id, after.column.id));
      return result;
    }
    private record GridHit(GridGeometry geo, GridSpan span, GridRecord row,
                           boolean gutter) {}
    private GridHit gridHit(int x, int y, int width, int height) {
      if (hits == null || hits.width() != width || hits.height() != height ||
          !hits.signature().equals(columnSignature()) || x < 0 || y < 0 ||
          x >= width || y >= height)
        return null;
      var geo = hits.geometry();
      var span = geo.columns()
                     .stream()
                     .filter(s -> s.x() <= x && x < s.x() + s.width())
                     .findFirst()
                     .orElse(null);
      if (y < geo.headerRows())
        return new GridHit(geo, span, null, false);
      int dy = y - geo.headerRows();
      if (dy % geo.stride() != 0 || y >= height - geo.footerRows())
        return null;
      int index = geo.top() + dy / geo.stride();
      var seen = hits.rows().get(index);
      if (seen == null)
        return null;
      var r = index < sourceSize() ? record(index) : null;
      if (r == null || !r.id.equals(seen)) {
        if (capture != null &&
            (capture.kind.equals("range") || capture.kind.equals("edit")))
          capture = null;
        return null;
      }
      boolean gutter = span == null && x < geo.gutter() && config.rowNumbers;
      return span == null && !gutter ? null : new GridHit(geo, span, r, gutter);
    }
    private GridEvent editPointer(String action, int x, int y, int width,
                                  int height, boolean extend) {
      var e = edit;
      if (e == null || e.pending || e.isNull ||
          !workValid(e.rowId, e.columnId, e.revision)) {
        capture = null;
        return new GridEvent();
      }
      if (action.equals("move") &&
          (capture == null || !capture.kind.equals("edit")))
        return new GridEvent();
      if (!List.of("down", "move", "click", "double").contains(action))
        return new GridEvent();
      var hit = gridHit(x, y, width, height);
      if (hit == null || hit.span() == null || hit.row() == null ||
          !hit.row().id.equals(e.rowId) || !hit.span().id().equals(e.columnId))
        return action.equals("move") ? new GridEvent()
                                     : new GridEvent("edit_blocked", "", "");
      var col = columns.stream()
                    .filter(c -> c.id.equals(hit.span().id()))
                    .findFirst()
                    .orElseThrow();
      int extra = config.showCellMarkers && info(hit.row(), col).state.edited
                      ? 2
                      : 0,
          pad = config.padding + extra,
          room = hit.span().width() - 2 * config.padding - extra;
      if (room <= 0)
        return new GridEvent();
      var buf = e.buffer;
      int start = editorWindow(buf.value(), buf.cursor, room).start(),
          offset = Math.max(0, Math.min(room, x - hit.span().x() - pad)),
          used = 0, pos = start;
      var gs = graphemes(buf.value());
      for (int i = start; i < gs.size(); i++) {
        int w = cells(clean(gs.get(i)));
        if (used + w > offset)
          break;
        used += w;
        pos++;
      }
      buf.select(extend || action.equals("move") ? buf.anchor : pos, pos);
      if (action.equals("down")) {
        var next = new GridCapture("edit");
        next.editId = e.id;
        armGrid(next, width, height);
      }
      return new GridEvent("edit_select", e.rowId, e.columnId);
    }
    public boolean pointerCaptured() { return capture != null; }
    public GridEvent pointer(String action, int x, int y, int width,
                             int height) {
      return pointer(action, x, y, width, height, false);
    }
    /**
     * Local grid coordinates. Route captured moves/releases outside the grid.
     */
    public GridEvent pointer(String action, int x, int y, int width, int height,
                             boolean extend) {
      mutation();
      if (action == null ||
          !List.of("down", "move", "up", "cancel", "click", "double",
                   "wheel_up", "wheel_down", "wheel_left", "wheel_right")
               .contains(action))
        return new GridEvent();
      gridNumber(x, -1000000000, 1000000000, "pointer x");
      gridNumber(y, -1000000000, 1000000000, "pointer y");
      gridNumber(width, 0, 65535, "width");
      gridNumber(height, 0, 4096, "height");
      var c = capture;
      if (c != null &&
          (c.width != width || c.height != height || c.revision != revision ||
           !c.signature.equals(columnSignature())))
        c = capture = null;
      if (config.disableMouse || paste != null || action.equals("cancel")) {
        capture = null;
        return new GridEvent();
      }
      if (action.equals("up")) {
        capture = null;
        if (c != null && c.kind.equals("column") && !c.moved) {
          var hit = gridHit(x, y, width, height);
          if (hit != null && hit.row() == null && hit.span() != null &&
              hit.span().id().equals(c.column))
            return click(x, y, width, height);
        }
        return new GridEvent();
      }
      if (action.equals("down"))
        c = capture = null;
      if (edit != null) {
        if (c != null && c.kind.equals("edit") && c.editId != edit.id)
          capture = null;
        return editPointer(action, x, y, width, height, extend);
      }
      if (action.startsWith("wheel_")) {
        capture = null;
        return handle(action.substring(6), height, "");
      }
      if (action.equals("move") && c == null)
        return new GridEvent();
      if (action.equals("move") && c.kind.equals("resize")) {
        String id = c.column;
        var col = columns.stream()
                      .filter(v -> v.id.equals(id))
                      .findFirst()
                      .orElseThrow();
        var o = columnConfig.getOrDefault(id, new GridColumnOptions());
        int value = Math.max(o.minWidth,
                             Math.min(o.maxWidth, c.startWidth + x - c.startX));
        if (value != col.width && resizeColumn(id, value)) {
          armGrid(c, width, height);
          return new GridEvent("resize", "", id);
        }
        return new GridEvent();
      }
      if (action.equals("move") && c.kind.equals("column")) {
        String id = c.column;
        var span = geometry(width, height)
                       .columns()
                       .stream()
                       .filter(s -> s.x() <= x && x < s.x() + s.width())
                       .findFirst()
                       .orElse(null);
        if (span != null && !span.id().equals(id)) {
          int source = -1, target = -1;
          for (int i = 0; i < columns.size(); i++) {
            if (columns.get(i).id.equals(id))
              source = i;
            if (columns.get(i).id.equals(span.id()))
              target = i;
          }
          if (source >= 0 && target >= 0 &&
              columns.get(source).pin.equals(columns.get(target).pin)) {
            var order = new ArrayList<>(columns);
            var value = order.remove(source);
            order.add(target, value);
            setColumnLayout(order);
            c.moved = true;
            armGrid(c, width, height);
            return new GridEvent("columns", "", id);
          }
        }
        return new GridEvent();
      }
      var hit = gridHit(x, y, width, height);
      if (hit == null)
        return new GridEvent();
      if (hit.row() == null) {
        if (action.equals("down")) {
          if (config.verticalLines && !config.disableResize)
            for (var s : hit.geo().columns())
              if (s.x() + s.width() == x) {
                var col = columns.stream()
                              .filter(v -> v.id.equals(s.id()))
                              .findFirst()
                              .orElseThrow();
                var next = new GridCapture("resize");
                next.column = s.id();
                next.startX = x;
                next.startWidth = col.width;
                armGrid(next, width, height);
                return new GridEvent("resize_start", "", s.id());
              }
          if (hit.span() != null) {
            var next = new GridCapture("column");
            next.column = hit.span().id();
            armGrid(next, width, height);
          }
          return new GridEvent();
        }
        return action.equals("click") || action.equals("double")
            ? click(x, y, width, height)
            : new GridEvent();
      }
      if (action.equals("move") && !c.kind.equals("range"))
        return new GridEvent();
      var p = current();
      var cs = visibleColumns();
      String id = hit.span() != null ? hit.span().id()
                  : p != null        ? p.column.id
                                     : "";
      var col =
          cs.stream().filter(v -> v.id.equals(id)).findFirst().orElse(null);
      if (col == null || info(hit.row(), col).state.disabled)
        return new GridEvent();
      String[] anchor = extend && p != null ? rangeAnchor(p)
                                            : new String[] {hit.row().id, id};
      boolean whole = hit.gutter() || config.selection.equals("row");
      if (action.equals("move")) {
        int index = sourceIndex(c.anchorRow).orElse(-1);
        if (index < 0 || index != c.anchorIndex ||
            !record(index).id.equals(c.anchorRow)) {
          capture = null;
          return new GridEvent();
        }
        anchor = new String[] {c.anchorRow, c.anchorColumn};
        whole = c.whole;
      }
      if (!focus(hit.row().id, id))
        return new GridEvent();
      if (action.equals("double"))
        return handle("activate", height, "");
      if (whole || extend || action.equals("move"))
        setSelection(new GridRange(anchor[0], whole ? cs.get(0).id : anchor[1],
                                   hit.row().id,
                                   whole ? cs.get(cs.size() - 1).id : id));
      else if (action.equals("down") || action.equals("click"))
        selected = null;
      if (action.equals("down")) {
        var next = new GridCapture("range");
        next.anchorRow = anchor[0];
        next.anchorColumn = anchor[1];
        next.anchorIndex = sourceIndex(anchor[0]).orElse(-1);
        next.whole = whole;
        armGrid(next, width, height);
      }
      return new GridEvent("select", hit.row().id, id);
    }
    public GridViewState saveView() {
      var p = current();
      var s = new GridViewState();
      for (var c : columns) s.columns.add(c.copy());
      columnConfig.forEach((k, v) -> s.columnOptions.put(k, v.copy()));
      s.rowId = p == null ? "" : p.row.id;
      s.columnId = p == null ? "" : p.column.id;
      s.topRowId = top < sourceSize() ? record(top).id : "";
      var normal = visibleColumns().stream().filter(c -> c.pin.isEmpty()).toList();
      s.leftColumnId = left < normal.size() ? normal.get(left).id : "";
      s.sortColumn = sortColumn;
      s.sortDirection = sortDirection;
      s.selection = selected;
      s.mode = config.selection;
      s.filter = status.filter;
      return s;
    }
    public void restoreView(GridViewState state) {
      mutation();
      var temp = new Grid(columns, List.<GridRecord>of());
      temp.setColumnLayout(state.columns);
      for (var item : state.columns) {
        gridNumber(item.width, 1, 4096, "column width");
        temp.columns.stream().filter(c -> c.id.equals(item.id)).findFirst().orElseThrow().width =
            item.width;
      }
      state.columnOptions.forEach(temp::setColumnOptions);
      if (!List.of("cell", "row", "range").contains(state.mode)
          || !List.of("", "asc", "desc").contains(state.sortDirection)
          || !state.sortColumn.isEmpty()
              && columns.stream().noneMatch(c -> c.id.equals(state.sortColumn)))
        throw new IllegalArgumentException("invalid grid view state");
      int at = sourceIndex(state.topRowId).orElse(-1);
      if (at >= 0)
        record
      (at);
      if (state.selection != null) {
        var cs = temp.visibleColumns();
        for (var pair :
            List.of(List.of(state.selection.anchorRow(), state.selection.anchorColumn()),
                List.of(state.selection.endRow(), state.selection.endColumn()))) {
          int i = sourceIndex(pair.get(0)).orElse(-1);
          if (i < 0 || !record(i).id.equals(pair.get(0))
              || cs.stream().noneMatch(c -> c.id.equals(pair.get(1))))
            throw new IllegalArgumentException("unknown view range ID");
        }
      }
      invalidate();
      columns = temp.columns;
      columnConfig.clear();
      columnConfig.putAll(temp.columnConfig);
      config.selection = state.mode;
      top = Math.max(0, at);
      left = 0;
      var normal = visibleColumns().stream().filter(c -> c.pin.isEmpty()).toList();
      for (int i = 0; i < normal.size(); i++)
        if (normal.get(i).id.equals(state.leftColumnId))
          left = i;
      sortColumn = state.sortColumn;
      sortDirection = state.sortDirection;
      status.filter = state.filter;
      selected = state.selection;
      focus(state.rowId, state.columnId);
    }
  }
  public static final class DropError extends IllegalArgumentException {
    private static final long serialVersionUID = 1L;
    public final String reason;
    public DropError(String reason) {
      super(reason);
      this.reason = reason;
    }
  }
  public record DropRequest(String sourceId, String targetId, String position, String revision) {}
  @FunctionalInterface
  public interface DropPolicy {
    boolean allow(DropRequest request);
  }
  public static final class DragOptions {
    public int threshold;
    public boolean autoScroll, hoverExpand;
    public List<String> locked = new ArrayList<>();
    public DragOptions copy() {
      var o = new DragOptions();
      o.threshold = threshold;
      o.autoScroll = autoScroll;
      o.hoverExpand = hoverExpand;
      o.locked = new ArrayList<>(locked);
      return o;
    }
  }
  public record DragPointer(String action, int x, int y, int width, int height) {}
  public record
      DragLayout(int first, int scroll, Set<String> expanded, List<TabCell> tabs, List<Node> rows) {
    public DragLayout {
      expanded = Set.copyOf(expanded);
      tabs = List.copyOf(tabs);
      rows = rows.stream().map(Node::copy).toList();
    }
  }
  private static DragOptions dragOptions(DragOptions value) {
    var o = value == null ? new DragOptions() : value.copy();
    if (o.threshold < 0 || o.threshold > 1000000 || o.locked.size() > 65536
        || o.locked.stream().anyMatch(id -> id == null || id.isEmpty()))
      throw new DropError("options");
    return o;
  }
  private static String dragRevisionParts(List<String> parts) {
    long hash = 0xcbf29ce484222325L;
    for (var s : parts) {
      dialogText(s, 1000000);
      byte[] bytes = s.getBytes(java.nio.charset.StandardCharsets.UTF_8);
      byte[] prefix = (bytes.length + ":").getBytes(java.nio.charset.StandardCharsets.US_ASCII);
      for (byte b : prefix) {
        hash ^= b & 255;
        hash *= 1099511628211L;
      }
      for (byte b : bytes) {
        hash ^= b & 255;
        hash *= 1099511628211L;
      }
    }
    String hex = Long.toUnsignedString(hash, 16);
    return "0".repeat(16 - hex.length()) + hex;
  }
  private static List<Node> dragNodes(Tree model) {
    return model.nodes.stream()
        .map(n -> {
          var copy = n.copy();
          copy.branch = model.branches.contains(n.id);
          return copy;
        })
        .toList();
  }
  public static String dragRevision(Tabs model) {
    var parts = new ArrayList<String>();
    for (var t : model.items) {
      parts.add(t.id);
      parts.add(t.title);
      parts.add(String.valueOf(t.edited));
      parts.add(String.valueOf(t.closable));
      parts.add(String.valueOf(t.disabled));
    }
    return dragRevisionParts(parts);
  }
  public static String dragRevision(Tree model) {
    var parts = new ArrayList<String>();
    for (var n : dragNodes(model)) {
      parts.add(n.id);
      parts.add(n.parent);
      parts.add(n.name);
      parts.add(n.secondary);
      parts.add(n.icon);
      parts.add(n.asciiIcon);
      parts.add(n.count == null ? "" : String.valueOf(n.count));
      parts.add(String.valueOf(n.branch));
    }
    return dragRevisionParts(parts);
  }
  private static String dragStateRevision(Tabs model) {
    return dragRevisionParts(List.of(model.active, model.focused, String.valueOf(model.first)));
  }
  private static String dragStateRevision(Tree model) {
    var parts = new ArrayList<>(
        List.of(model.selected, String.valueOf(model.scroll), String.valueOf(model.horizontal)));
    parts.addAll(new TreeSet<>(model.expanded));
    return dragRevisionParts(parts);
  }
  private static Tabs dragCopyState(Tabs old, Tabs next) {
    next.active = old.active;
    next.focused = old.focused;
    next.first = old.first;
    next.reconcile();
    return next;
  }
  private static Tree dragCopyState(Tree old, Tree next) {
    next.selected = old.selected;
    next.scroll = old.scroll;
    next.horizontal = old.horizontal;
    for (var id : old.expanded)
      if (next.byId.containsKey(id))
        next.expanded.add(id);
    return next;
  }
  public static Tabs applyDrop(Tabs model, DropRequest request) {
    if (!request.revision().equals(dragRevision(model)))
      throw new DropError("stale");
    if (request.sourceId().equals(request.targetId()))
      throw new DropError("self");
    if (!List.of("before", "after").contains(request.position()))
      throw new DropError("position");
    var items = new ArrayList<>(model.items.stream().map(Tab::copy).toList());
    int source = -1, target = -1;
    for (int i = 0; i < items.size(); i++) {
      if (items.get(i).id.equals(request.sourceId()))
        source = i;
      if (items.get(i).id.equals(request.targetId()))
        target = i;
    }
    if (source < 0 || target < 0)
      throw new DropError("missing");
    if (items.get(source).disabled || items.get(target).disabled)
      throw new DropError("disabled");
    var item = items.remove(source);
    if (source < target)
      target--;
    if (request.position().equals("after"))
      target++;
    if (source == target)
      throw new DropError("unchanged");
    items.add(target, item);
    return dragCopyState(model, new Tabs(items));
  }
  public static Tree applyDrop(Tree model, DropRequest request) {
    if (!request.revision().equals(dragRevision(model)))
      throw new DropError("stale");
    var nodes = dragNodes(model);
    var index = new HashMap<String, Integer>();
    for (int i = 0; i < nodes.size(); i++) index.put(nodes.get(i).id, i);
    var source = index.get(request.sourceId());
    var target = index.get(request.targetId());
    if (source == null || target == null)
      throw new DropError("missing");
    if (source.equals(target))
      throw new DropError("self");
    if (!List.of("before", "after", "inside").contains(request.position()))
      throw new DropError("position");
    String parent = request.targetId();
    while (!parent.isEmpty()) {
      if (parent.equals(request.sourceId()))
        throw new DropError("cycle");
      parent = nodes.get(index.get(parent)).parent;
    }
    if (request.position().equals("inside") && !nodes.get(target).branch)
      throw new DropError("leaf");
    int end = source + 1;
    while (end < nodes.size()
        && model.depth.get(nodes.get(end).id) > model.depth.get(request.sourceId()))
      end++;
    int extra = 0;
    for (int i = source; i < end; i++)
      extra =
          Math.max(extra, model.depth.get(nodes.get(i).id) - model.depth.get(request.sourceId()));
    if (model.depth.get(request.targetId()) + (request.position().equals("inside") ? 1 : 0) + extra
        > 128)
      throw new DropError("depth");
    var block = new ArrayList<>(nodes.subList(source, end).stream().map(Node::copy).toList());
    var remaining = new ArrayList<>(nodes);
    remaining.subList(source, end).clear();
    int at = 0;
    while (!remaining.get(at).id.equals(request.targetId())) at++;
    parent = request.position().equals("inside") ? request.targetId() : remaining.get(at).parent;
    if (!request.position().equals("before")) {
      at++;
      while (at < remaining.size()
          && model.depth.get(remaining.get(at).id) > model.depth.get(request.targetId()))
        at++;
    }
    block.get(0).parent = parent;
    remaining.addAll(at, block);
    boolean same = true;
    for (int i = 0; same && i < nodes.size(); i++)
      same = remaining.get(i).id.equals(nodes.get(i).id)
          && remaining.get(i).parent.equals(nodes.get(i).parent);
    if (same)
      throw new DropError("unchanged");
    return dragCopyState(model, new Tree(remaining));
  }
  public static DropRequest requestDrop(Tabs model, String source, String target, String position,
      DragOptions value, DropPolicy allow) {
    var o = dragOptions(value);
    if (o.locked.contains(source) || o.locked.contains(target))
      throw new DropError("locked");
    var r = new DropRequest(source, target, position, dragRevision(model));
    applyDrop(model, r);
    if (allow != null) {
      boolean accepted;
      try {
        accepted = allow.allow(r);
      } catch (RuntimeException error) {
        throw new DropError("policy");
      }
      if (!accepted)
        throw new DropError("policy");
      if (!r.revision().equals(dragRevision(model)))
        throw new DropError("stale");
    }
    return r;
  }
  public static DropRequest requestDrop(Tree model, String source, String target, String position,
      DragOptions value, DropPolicy allow) {
    var o = dragOptions(value);
    if (o.locked.contains(source) || o.locked.contains(target))
      throw new DropError("locked");
    var r = new DropRequest(source, target, position, dragRevision(model));
    applyDrop(model, r);
    if (allow != null) {
      boolean accepted;
      try {
        accepted = allow.allow(r);
      } catch (RuntimeException error) {
        throw new DropError("policy");
      }
      if (!accepted)
        throw new DropError("policy");
      if (!r.revision().equals(dragRevision(model)))
        throw new DropError("stale");
    }
    return r;
  }
  public static DropRequest keyboardDrop(
      Tabs model, String direction, DragOptions o, DropPolicy allow) {
    int i = 0;
    while (i < model.items.size() && !model.items.get(i).id.equals(model.focused)) i++;
    if (i == model.items.size())
      throw new DropError("missing");
    if (!List.of("previous", "next").contains(direction))
      throw new DropError("position");
    int j = i + (direction.equals("previous") ? -1 : 1);
    if (j < 0 || j >= model.items.size())
      throw new DropError("missing");
    return requestDrop(model, model.focused, model.items.get(j).id,
        direction.equals("previous") ? "before" : "after", o, allow);
  }
  public static DropRequest keyboardDrop(
      Tree model, String direction, DragOptions o, DropPolicy allow) {
    var source = model.byId.get(model.selected);
    if (source == null)
      throw new DropError("missing");
    if (direction.equals("outside") && !source.parent.isEmpty())
      return requestDrop(model, source.id, source.parent, "after", o, allow);
    var siblings = model.nodes.stream().filter(n -> n.parent.equals(source.parent)).toList();
    int i = 0;
    while (!siblings.get(i).id.equals(source.id)) i++;
    if (!List.of("previous", "next", "inside").contains(direction))
      throw new DropError("position");
    int j = i + (direction.equals("next") ? 1 : -1);
    if (j < 0 || j >= siblings.size())
      throw new DropError("missing");
    return requestDrop(model, source.id, siblings.get(j).id,
        direction.equals("inside")     ? "inside"
            : direction.equals("next") ? "after"
                                       : "before",
        o, allow);
  }
  /** Captured request-only drag gestures. The host approves and installs replacements. */
  public static final class DragState {
    public boolean enabled;
    public String phase = "idle", result = "", sourceId = "", targetId = "", position = "",
                  reason = "";
    public boolean allowed;
    private boolean busy;
    private String renderKey = "", revision = "", stateRevision = "";
    private int downX, downY, width, height, first, scroll;
    private Set<String> expanded = new HashSet<>();
    private DropRequest request;
    private DragPointer last = new DragPointer("cancel", 0, 0, 0, 0);
    public DragState() {}
    public DragState(boolean enabled) {
      this.enabled = enabled;
    }
    public boolean captured() {
      return phase.equals("armed") || phase.equals("dragging");
    }
    private void reset(String outcome) {
      phase = "idle";
      result = outcome;
      sourceId = targetId = position = reason = revision = stateRevision = "";
      allowed = false;
      downX = downY = width = height = first = scroll = 0;
      expanded.clear();
      request = null;
      last = new DragPointer("cancel", 0, 0, 0, 0);
    }
    public void cancel() {
      if (busy)
        throw new DropError("reentrant");
      reset("cancel");
    }
    public void renderKey(String key) {
      if (busy)
        throw new DropError("reentrant");
      if (key == null)
        throw new DropError("bounds");
      if (captured() && !renderKey.isEmpty() && !renderKey.equals(key))
        reset("stale");
      renderKey = key;
    }
    private static void bounds(int value, int min, int max, String error) {
      if (value < min || value > max)
        throw new DropError(error);
    }
    private static String revision(Object model) {
      return model instanceof Tabs t ? dragRevision(t) : dragRevision((Tree) model);
    }
    private static String stateRevision(Object model) {
      return model instanceof Tabs t ? dragStateRevision(t) : dragStateRevision((Tree) model);
    }
    private boolean valid(Object model, int w, int h) {
      if (!captured())
        return false;
      if (!enabled) {
        reset("cancel");
        return false;
      }
      if (width != w || height != h || !revision.equals(revision(model))
          || !stateRevision.equals(stateRevision(model))) {
        reset("stale");
        return false;
      }
      return true;
    }
    private static Tabs copy(Tabs model) {
      return dragCopyState(model, new Tabs(model.items));
    }
    private static Tree copy(Tree model) {
      return dragCopyState(model, new Tree(dragNodes(model)));
    }
    private List<TabCell> tabCells(Tabs model, int w, int start) {
      var out = new ArrayList<TabCell>();
      int x = 1;
      if (w <= 2)
        return out;
      for (int i = Math.max(0, start); i < model.items.size() && x < w - 1; i++) {
        var t = model.items.get(i);
        int extent = Math.min(Tabs.itemWidth(t), w - 1 - x);
        if (extent < 4 && !out.isEmpty())
          break;
        boolean active = t.id.equals(model.active), focused = t.id.equals(model.focused);
        String suffix = (t.edited ? " *" : "") + (t.closable ? " x" : "");
        String text = clip((focused ? ">" : " ") + (active ? "[" : " ")
                + clip(t.title, Math.max(0, extent - 3 - suffix.length()), true) + suffix
                + (active ? "]" : " "),
            extent, true);
        out.add(new TabCell(t.id, text, x, extent, active, focused, t.disabled));
        x += extent;
      }
      return out;
    }
    private List<Node> treeRows(Tree model, int h) {
      var preview = copy(model);
      preview.expanded.clear();
      preview.expanded.addAll(expanded);
      var rows = preview.visible();
      scroll = Math.max(0, Math.min(scroll, rows.size() - Math.max(1, h)));
      return rows;
    }
    public DragLayout previewLayout(Tabs model, int w, int h) {
      return preview(model, w, h);
    }
    public DragLayout previewLayout(Tree model, int w, int h) {
      return preview(model, w, h);
    }
    private DragLayout preview(Object model, int w, int h) {
      if (busy)
        throw new DropError("reentrant");
      bounds(w, 0, 65535, "bounds");
      bounds(h, 0, 4096, "bounds");
      if (!valid(model, w, h)) {
        if (model instanceof Tabs t) {
          var p = copy(t);
          var cells = p.layout(w);
          return new DragLayout(p.first, 0, Set.of(), cells, List.of());
        }
        var p = copy((Tree) model);
        var rows = p.reconcile(h);
        return new DragLayout(0, p.scroll, p.expanded, List.of(), rows);
      }
      if (model instanceof Tabs t)
        return new DragLayout(first, 0, Set.of(), tabCells(t, w, first), List.of());
      var rows = treeRows((Tree) model, h);
      return new DragLayout(0, scroll, expanded, List.of(), rows);
    }
    public DropRequest pointer(Tabs model, DragPointer p) {
      return pointer(model, p, null, null);
    }
    public DropRequest pointer(Tree model, DragPointer p) {
      return pointer(model, p, null, null);
    }
    public DropRequest pointer(Tabs model, DragPointer p, DragOptions options, DropPolicy policy) {
      return point(model, p, options, policy);
    }
    public DropRequest pointer(Tree model, DragPointer p, DragOptions options, DropPolicy policy) {
      return point(model, p, options, policy);
    }
    private DropRequest point(Object model, DragPointer p, DragOptions options, DropPolicy policy) {
      if (busy)
        throw new DropError("reentrant");
      var o = dragOptions(options);
      if (p == null || !List.of("down", "move", "up", "cancel").contains(p.action()))
        throw new DropError("pointer");
      bounds(p.x(), -1000000000, 1000000000, "pointer");
      bounds(p.y(), -1000000000, 1000000000, "pointer");
      bounds(p.width(), 0, 65535, "pointer");
      bounds(p.height(), 0, 4096, "pointer");
      if (p.action().equals("cancel")) {
        cancel();
        return null;
      }
      if (!enabled) {
        if (captured())
          reset("cancel");
        return null;
      }
      if (p.action().equals("down")) {
        reset("");
        if (p.x() < 0 || p.x() >= p.width() || p.y() < 0 || p.y() >= p.height())
          return null;
        String id = "";
        int f = 0, s = 0;
        Set<String> e = new HashSet<>();
        if (model instanceof Tabs t) {
          if (p.y() != 0)
            return null;
          var preview = copy(t);
          for (var c : preview.layout(p.width()))
            if (c.start() <= p.x() && p.x() < c.start() + c.width() && !c.disabled()) {
              id = c.id();
              break;
            }
          f = preview.first;
        } else {
          var preview = copy((Tree) model);
          var rows = preview.reconcile(p.height());
          int i = preview.scroll + p.y();
          if (i < rows.size())
            id = rows.get(i).id;
          s = preview.scroll;
          e = new HashSet<>(preview.expanded);
        }
        if (id.isEmpty() || o.locked.contains(id))
          return null;
        phase = "armed";
        sourceId = id;
        revision = revision(model);
        stateRevision = stateRevision(model);
        downX = p.x();
        downY = p.y();
        width = p.width();
        height = p.height();
        first = f;
        scroll = s;
        expanded = e;
        last = p;
        return null;
      }
      if (!valid(model, p.width(), p.height()))
        return null;
      last = p;
      if (Math.max(Math.abs(p.x() - downX), Math.abs(p.y() - downY))
          >= (o.threshold == 0 ? 2 : o.threshold))
        phase = "dragging";
      if (phase.equals("dragging")) {
        DropRequest raw = null;
        String error = "outside";
        if (model instanceof Tabs t) {
          if (o.autoScroll && p.action().equals("move")) {
            if (p.x() <= 0)
              first = Math.max(0, first - 1);
            else if (p.x() >= p.width() - 1)
              first = Math.min(Math.max(0, t.items.size() - 1), first + 1);
          }
          for (var c : tabCells(t, p.width(), first))
            if (p.x() >= 0 && p.x() < p.width() && p.y() == 0 && c.start() <= p.x()
                && p.x() < c.start() + c.width()) {
              raw = new DropRequest(sourceId, c.id(),
                  p.x() - c.start() >= c.width() / 2 ? "after" : "before", revision);
              break;
            }
        } else {
          var t = (Tree) model;
          var rows = treeRows(t, p.height());
          if (o.autoScroll && p.action().equals("move")) {
            if (p.y() <= 0)
              scroll = Math.max(0, scroll - 1);
            else if (p.y() >= p.height() - 1)
              scroll = Math.min(Math.max(0, rows.size() - Math.max(1, p.height())), scroll + 1);
          }
          int i = scroll + p.y();
          if (p.x() >= 0 && p.x() < p.width() && p.y() >= 0 && p.y() < p.height() && i >= 0
              && i < rows.size()) {
            var target = rows.get(i);
            String pos = p.x() <= 2 + t.depth.get(target.id) * 2          ? "before"
                : t.branches.contains(target.id) && p.x() < p.width() - 2 ? "inside"
                                                                          : "after";
            raw = new DropRequest(sourceId, target.id, pos, revision);
          }
        }
        if (raw != null) {
          busy = true;
          try {
            if (model instanceof Tabs t)
              requestDrop(t, raw.sourceId(), raw.targetId(), raw.position(), o, policy);
            else
              requestDrop((Tree) model, raw.sourceId(), raw.targetId(), raw.position(), o, policy);
            error = "";
          } catch (DropError failure) {
            error = failure.reason;
          } finally {
            busy = false;
          }
          if (!valid(model, p.width(), p.height()))
            return null;
        }
        request = raw;
        targetId = raw == null ? "" : raw.targetId();
        position = raw == null ? "" : raw.position();
        allowed = error.isEmpty();
        reason = error;
        if (model instanceof Tree && raw != null && allowed && o.hoverExpand
            && position.equals("inside"))
          expanded.add(targetId);
      }
      if (!p.action().equals("up"))
        return null;
      var out = phase.equals("dragging") && allowed ? request : null;
      String outcome = out != null ? "drop" : phase.equals("dragging") ? "reject" : "";
      reset(outcome);
      return out;
    }
    public void draw(Tabs model, Canvas canvas, Rect r, boolean focused, boolean ascii) {
      paint(model, canvas, r, focused, ascii);
    }
    public void draw(Tree model, Canvas canvas, Rect r, boolean focused, boolean ascii) {
      paint(model, canvas, r, focused, ascii);
    }
    private void paint(Object model, Canvas canvas, Rect r, boolean focused, boolean ascii) {
      if (busy)
        throw new DropError("reentrant");
      bounds(r.x(), 0, 1000000000, "bounds");
      bounds(r.y(), 0, 1000000000, "bounds");
      bounds(r.width(), 0, 65535, "bounds");
      bounds(r.height(), 0, 4096, "bounds");
      if (!focused && captured())
        reset("cancel");
      renderKey(r.x() + "|" + r.y() + "|" + r.width() + "|" + r.height() + "|"
          + canvas.palette.theme + "|" + canvas.palette.profile + "|" + canvas.surfaceRole + "|"
          + focused + "|" + ascii);
      if (!valid(model, r.width(), r.height())) {
        if (model instanceof Tabs t)
          t.draw(canvas, r, focused, ascii);
        else
          ((Tree) model).draw(canvas, r, focused, ascii);
        return;
      }
      var child = new Canvas(r.width(), r.height(), canvas.palette, canvas.surfaceRole);
      int mx = 0, my = 0;
      String marker = "!";
      if (model instanceof Tabs t) {
        var views = tabCells(t, r.width(), first);
        if (first > 0)
          child.write(0, 0, "<", "hint");
        if (first + views.size() < t.items.size() && r.width() > 0)
          child.write(r.width() - 1, 0, ">", "hint");
        for (var c : views) {
          String role = c.disabled() ? "disabled" : c.active() ? "selection" : "body";
          child.write(c.start(), 0, " ".repeat(c.width()), role, focused && c.focused(), c.width());
          child.write(c.start(), 0, c.text(), role, focused && c.focused(), c.width());
        }
        var target = views.stream().filter(c -> c.id().equals(targetId)).findFirst();
        mx = target.isEmpty()
            ? Math.max(0, Math.min(r.width() - 1, last.x()))
            : target.get().start() + (position.equals("after") ? target.get().width() - 1 : 0);
        marker = ascii ? "|" : "│";
      } else {
        var t = (Tree) model;
        var rows = treeRows(t, r.height());
        for (int y = 0; y < r.height() && scroll + y < rows.size(); y++) {
          var n = rows.get(scroll + y);
          boolean selected = t.selected.equals(n.id);
          String arrow = t.branches.contains(n.id) ? expanded.contains(n.id) ? ascii ? "v" : "▾"
                  : ascii                                                    ? ">"
                                                                             : "▸"
                                                   : " ";
          String icon = ascii ? n.asciiIcon : n.icon;
          String text = " ".repeat(t.depth.get(n.id) * 2) + arrow + " "
              + (icon.isEmpty() ? "" : icon + " ") + n.name
              + (n.secondary.isEmpty() ? "" : "  " + n.secondary)
              + (n.count == null ? "" : " (" + n.count + ")");
          var gs = graphemes(text);
          int start = 0, skipped = 0;
          while (start < gs.size() && skipped < t.horizontal) skipped += cells(gs.get(start++));
          var out = new StringBuilder();
          for (int i = start; i < gs.size(); i++) out.append(gs.get(i));
          child.write(0, y,
              (selected ? "> " : "  ") + clip(out.toString(), Math.max(0, r.width() - 2), true),
              selected ? "selection" : "body", focused && selected, r.width());
        }
        int at = -1;
        for (int i = 0; i < rows.size(); i++)
          if (rows.get(i).id.equals(targetId)) {
            at = i;
            break;
          }
        my = at < 0 ? Math.max(0, Math.min(r.height() - 1, last.y())) : at - scroll;
        marker = position.equals("before") ? ascii ? "^" : "↑"
            : position.equals("after")     ? ascii ? "v" : "↓"
            : position.equals("inside")    ? ascii ? "+" : "↳"
                                           : "!";
      }
      if (phase.equals("dragging") && mx >= 0 && mx < r.width() && my >= 0 && my < r.height()) {
        var old = child.data[my][mx].style;
        var semantic = child.palette.style(allowed ? "info" : "error");
        int fg = semantic.foreground;
        if (colorContrast(fg, old.background) < 4.5
            && colorContrast(old.foreground, old.background) > colorContrast(fg, old.background))
          fg = old.foreground;
        child.writeStyle(mx, my, allowed ? marker : "!",
            new Style(fg, old.background, true, false, true, false), 1);
      }
      canvas.blit(child, new Rect(0, 0, r.width(), r.height()), r.x(), r.y());
    }
  }
  public record InputEvent(String key, String text, int x, int y, int button) {
    public InputEvent(String key) {
      this(key, "", 0, 0, 0);
    }
    public InputEvent(String key, String text) {
      this(key, text, 0, 0, 0);
    }
  }
  /** Incremental UTF-8 input without native or terminal dependencies. */
  public static final class InputDecoder {
    private byte[] bytes = new byte[0];
    private int offset;
    private java.io.ByteArrayOutputStream paste;
    private boolean rejected;
    private static final int LIMIT = 16 * 1024 * 1024;
    private static final String[][] KEYS = {{"\033[A", "up"}, {"\033[B", "down"},
        {"\033[C", "right"}, {"\033[D", "left"}, {"\033[H", "home"}, {"\033[F", "end"},
        {"\033[5~", "page_up"}, {"\033[6~", "page_down"}, {"\033[3~", "delete"},
        {"\033[Z", "shift_tab"}, {"\033OP", "f1"}, {"\033OQ", "f2"}, {"\033[21~", "f10"},
        {"\033[21;2~", "shift_f10"}};
    public void feed(byte[] chunk) {
      if (chunk == null)
        throw new IllegalArgumentException("input requires bytes");
      if ((long) bytes.length - offset + chunk.length > LIMIT + 64) {
        bytes = new byte[0];
        offset = 0;
        paste = null;
        rejected = true;
        return;
      }
      var next = new byte[bytes.length - offset + chunk.length];
      System.arraycopy(bytes, offset, next, 0, bytes.length - offset);
      System.arraycopy(chunk, 0, next, bytes.length - offset, chunk.length);
      bytes = next;
      offset = 0;
    }
    public boolean waitingEscape() {
      return paste == null && offset < bytes.length && bytes[offset] == 27;
    }
    private boolean starts(String s) {
      if (bytes.length - offset < s.length())
        return false;
      for (int i = 0; i < s.length(); i++)
        if ((bytes[offset + i] & 255) != s.charAt(i))
          return false;
      return true;
    }
    private boolean prefix(String s) {
      int size = bytes.length - offset;
      if (size > s.length())
        return false;
      for (int i = 0; i < size; i++)
        if ((bytes[offset + i] & 255) != s.charAt(i))
          return false;
      return true;
    }
    public InputEvent next() {
      return next(false);
    }
    public InputEvent next(boolean flushEscape) {
      if (rejected) {
        rejected = false;
        return new InputEvent("paste_rejected");
      }
      if (paste != null) {
        int end = -1;
        for (int i = offset; i + 6 <= bytes.length; i++)
          if (bytes[i] == 27 && bytes[i + 1] == '[' && bytes[i + 2] == '2' && bytes[i + 3] == '0'
              && bytes[i + 4] == '1' && bytes[i + 5] == '~') {
            end = i;
            break;
          }
        int count = end < 0 ? Math.max(0, bytes.length - offset - 5) : end - offset;
        if ((long) paste.size() + count > LIMIT) {
          bytes = new byte[0];
          offset = 0;
          paste = null;
          return new InputEvent("paste_rejected");
        }
        paste.write(bytes, offset, count);
        offset += count;
        if (end < 0)
          return null;
        String text = paste.toString(java.nio.charset.StandardCharsets.UTF_8);
        paste = null;
        offset += 6;
        return new InputEvent("paste", text);
      }
      if (offset >= bytes.length)
        return null;
      if (starts("\033[200~")) {
        offset += 6;
        paste = new java.io.ByteArrayOutputStream();
        return next(flushEscape);
      }
      if (starts("\033[<")) {
        int end = -1;
        for (int i = offset + 3; i < bytes.length; i++)
          if (bytes[i] == 'M' || bytes[i] == 'm') {
            end = i;
            break;
          }
        if (end >= 0) {
          String raw = new String(
              bytes, offset + 3, end - offset - 3, java.nio.charset.StandardCharsets.US_ASCII);
          boolean release = bytes[end] == 'm';
          offset = end + 1;
          var fields = raw.split(";", -1);
          long[] values = new long[3];
          boolean valid = fields.length == 3;
          if (valid)
            for (int i = 0; i < 3; i++) {
              if (fields[i].isEmpty() || !fields[i].chars().allMatch(c -> c >= '0' && c <= '9')) {
                valid = false;
                break;
              }
              try {
                values[i] = Long.parseLong(fields[i]);
              } catch (NumberFormatException failure) {
                valid = false;
                break;
              }
            }
          if (!valid || values[0] > 1000000000 || values[1] < 1 || values[1] > 1000000001
              || values[2] < 1 || values[2] > 1000000001)
            return new InputEvent("unknown");
          int button = (int) values[0];
          return new InputEvent(release ? "mouse_release"
                  : (button & 64) != 0  ? "wheel"
                  : (button & 32) != 0  ? "mouse_move"
                                        : "mouse",
              "", (int) (values[1] - 1), (int) (values[2] - 1), button);
        }
      }
      for (var k : KEYS)
        if (starts(k[0])) {
          offset += k[0].length();
          return new InputEvent(k[1]);
        }
      int first = bytes[offset] & 255;
      if (first == 27) {
        boolean incomplete = prefix("\033[200~");
        for (var k : KEYS) incomplete |= prefix(k[0]);
        incomplete |= starts("\033[<");
        if (incomplete && !flushEscape)
          return null;
        if (bytes.length - offset > 1 && bytes[offset + 1] == '[')
          for (int i = offset + 2; i < bytes.length; i++)
            if (bytes[i] >= 0x40 && bytes[i] <= 0x7e) {
              offset = i + 1;
              return new InputEvent("unknown");
            }
        offset++;
        return new InputEvent("escape");
      }
      if (first < 32 || first == 127) {
        offset++;
        String key = switch (first) {
          case 9 -> "tab";
          case 10, 13 -> "enter";
          case 8, 127 -> "backspace";
          default -> "ctrl_" + (char) (first + 96);
        };
        return new InputEvent(key);
      }
      int n = first < 128                  ? 1
          : first >= 0xc2 && first <= 0xdf ? 2
          : first >= 0xe0 && first <= 0xef ? 3
          : first >= 0xf0 && first <= 0xf4 ? 4
                                           : 0;
      if (n == 0) {
        offset++;
        return new InputEvent("text", "\ufffd");
      }
      if (bytes.length - offset < n)
        return null;
      int cp = first & (n == 1 ? 127 : n == 2 ? 31 : n == 3 ? 15 : 7);
      boolean valid = true;
      for (int i = 1; i < n; i++) {
        int c = bytes[offset + i] & 255;
        if ((c & 0xc0) != 0x80) {
          valid = false;
          break;
        }
        cp = (cp << 6) | (c & 63);
      }
      if (!valid || cp > 0x10ffff || (cp >= 0xd800 && cp <= 0xdfff) || (n == 2 && cp < 128)
          || (n == 3 && cp < 2048) || (n == 4 && cp < 65536)) {
        offset++;
        return new InputEvent("text", "\ufffd");
      }
      String text = new String(bytes, offset, n, java.nio.charset.StandardCharsets.UTF_8);
      offset += n;
      return new InputEvent("text", text);
    }
  }
  /** Optional POSIX session using the OS stty utility, without JNI/foreign engines. */
  public static final class Terminal implements AutoCloseable {
    private final boolean mouse, mouseMotion;
    private final InputDecoder decoder = new InputDecoder();
    private volatile boolean active;
    private boolean closed, reading, eof;
    private String saved = "";
    private long escapeAt, sizeAt;
    private int columns = 80, rows = 24, reportedColumns = 80, reportedRows = 24;
    private Thread hook;
    public Terminal() {
      this(true, false);
    }
    public Terminal(boolean mouse, boolean mouseMotion) {
      this.mouse = mouse;
      this.mouseMotion = mouseMotion;
    }
    private static String stty(String... args) throws java.io.IOException {
      var command = new ArrayList<String>();
      command.add("stty");
      command.addAll(List.of(args));
      Process process =
          new ProcessBuilder(command).redirectInput(new java.io.File("/dev/tty")).start();
      boolean interrupted = Thread.interrupted();
      long deadline = System.nanoTime() + 2_000_000_000L;
      try {
        while (true) {
          try {
            if (process.waitFor(Math.max(1, deadline - System.nanoTime()),
                    java.util.concurrent.TimeUnit.NANOSECONDS))
              break;
            process.destroyForcibly();
            throw new java.io.IOException("stty timed out");
          } catch (InterruptedException failure) {
            interrupted = true;
            if (System.nanoTime() >= deadline) {
              process.destroyForcibly();
              throw new java.io.IOException("stty interrupted", failure);
            }
          }
        }
        if (process.exitValue() != 0)
          throw new java.io.IOException("POSIX stty failed: "
              + new String(process.getErrorStream().readNBytes(4096),
                  java.nio.charset.StandardCharsets.UTF_8));
        return new String(
            process.getInputStream().readNBytes(4096), java.nio.charset.StandardCharsets.US_ASCII)
            .strip();
      } finally {
        if (interrupted)
          Thread.currentThread().interrupt();
        process.getInputStream().close();
        process.getErrorStream().close();
        process.getOutputStream().close();
      }
    }
    public synchronized Terminal open() throws java.io.IOException {
      if (active || closed)
        throw new IllegalStateException("Terminal session cannot be reopened");
      if (System.console() == null || !new java.io.File("/dev/tty").exists())
        throw new java.io.IOException("interactive Terminal requires a POSIX TTY");
      saved = stty("-g");
      if (saved.isEmpty() || saved.chars().anyMatch(Character::isWhitespace))
        throw new java.io.IOException("invalid stty state");
      stty("raw", "-echo");
      active = true;
      try {
        hook = new Thread(() -> {
          try {
            close();
          } catch (java.io.IOException ignored) {
          }
        }, "tuivory-terminal-restore");
        Runtime.getRuntime().addShutdownHook(hook);
        write("\033[?1049h\033[?2004h"
            + (mouse ? (mouseMotion ? "\033[?1002h" : "\033[?1000h") + "\033[?1006h" : ""));
        int[] initial = size();
        reportedColumns = initial[0];
        reportedRows = initial[1];
      } catch (RuntimeException | java.io.IOException failure) {
        try {
          close();
        } catch (java.io.IOException cleanup) {
          failure.addSuppressed(cleanup);
        }
        throw failure;
      }
      return this;
    }
    public synchronized int[] size() throws java.io.IOException {
      long now = System.nanoTime();
      if (active && now - sizeAt > 250_000_000L) {
        String[] values = stty("size").split("\\s+");
        if (values.length == 2)
          try {
            int r = Integer.parseInt(values[0]), c = Integer.parseInt(values[1]);
            if (r > 0 && c > 0) {
              rows = r;
              columns = c;
            }
          } catch (NumberFormatException failure) {
            throw new java.io.IOException("invalid stty size", failure);
          }
        sizeAt = now;
      }
      return new int[] {columns, rows};
    }
    public void write(String text) throws java.io.IOException {
      if (!active)
        throw new IllegalStateException("Terminal is closed");
      System.out.write(text.getBytes(java.nio.charset.StandardCharsets.UTF_8));
      System.out.flush();
      if (System.out.checkError())
        throw new java.io.IOException("terminal output failed");
    }
    public InputEvent read() throws java.io.IOException, InterruptedException {
      return read(100);
    }
    public InputEvent read(int timeoutMillis) throws java.io.IOException, InterruptedException {
      if (timeoutMillis < 0 || timeoutMillis > 3600000)
        throw new IllegalArgumentException("invalid terminal timeout");
      synchronized (this) {
        if (!active)
          return new InputEvent("eof");
        if (reading)
          throw new IllegalStateException("only one terminal read may be pending");
        reading = true;
      }
      long deadline = System.nanoTime() + timeoutMillis * 1_000_000L;
      try {
        while (active) {
          int[] current = size();
          if (reportedColumns != current[0] || reportedRows != current[1]) {
            reportedColumns = current[0];
            reportedRows = current[1];
            return new InputEvent("resize", "", current[0], current[1], 0);
          }
          long now = System.nanoTime();
          InputEvent event =
              decoder.next(decoder.waitingEscape() && now - escapeAt >= 100_000_000L);
          if (event != null) {
            if (decoder.waitingEscape())
              escapeAt = now;
            return event;
          }
          if (eof)
            return new InputEvent("eof");
          int available = System.in.available();
          if (available > 0) {
            byte[] input = new byte[Math.min(8192, available)];
            int n = System.in.read(input);
            if (n < 0)
              eof = true;
            else {
              if (!decoder.waitingEscape())
                escapeAt = System.nanoTime();
              decoder.feed(Arrays.copyOf(input, n));
            }
            continue;
          }
          if (now >= deadline)
            return null;
          Thread.sleep(Math.min(10, Math.max(1, (deadline - now) / 1_000_000L)));
        }
        return new InputEvent("eof");
      } finally {
        synchronized (this) {
          reading = false;
        }
      }
    }
    @Override
    public synchronized void close() throws java.io.IOException {
      if (!active)
        return;
      active = false;
      closed = true;
      java.io.IOException error = null;
      try {
        System.out.write(
            "\033[0m\033[?1000l\033[?1002l\033[?1006l\033[?2004l\033[?25h\033[?1049l".getBytes(
                java.nio.charset.StandardCharsets.US_ASCII));
        System.out.flush();
      } catch (java.io.IOException failure) {
        error = failure;
      }
      try {
        stty(saved);
      } catch (java.io.IOException failure) {
        if (error == null)
          error = failure;
        else
          error.addSuppressed(failure);
      } finally {
        if (hook != null && Thread.currentThread() != hook)
          try {
            Runtime.getRuntime().removeShutdownHook(hook);
          } catch (IllegalStateException ignored) {
          }
        hook = null;
      }
      if (error != null)
        throw error;
    }
  }
}
