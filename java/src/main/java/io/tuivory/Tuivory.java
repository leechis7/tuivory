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
  public record
      Style(int foreground, int background, boolean bold, boolean dim, boolean underline) {
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
          + (bold ? ";1" : "") + (dim ? ";2" : "") + (underline ? ";4" : "") + "m";
    }
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
      int[] t = Data.PALETTES[(theme * 4 + profile) * 16 + index];
      return new Style(t[0], t[1], t[2] != 0, role.equals("disabled"), focused);
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
    public final Cell[][] data;
    public int cursorX = -1, cursorY = -1;
    public Canvas(int width, int height) {
      this(width, height, new Palette());
    }
    public Canvas(int width, int height, Palette palette) {
      if (width < 0 || height < 0 || (long) width * height > 1_000_000)
        throw new IllegalArgumentException("invalid dimensions");
      this.width = width;
      this.height = height;
      this.palette = palette;
      data = new Cell[height][width];
      for (var row : data)
        for (int x = 0; x < width; x++) row[x] = new Cell(palette.style("surface"));
    }
    private void erase(int x, int y) {
      var row = data[y];
      int start = row[x].owner >= 0 ? row[x].owner : x, end = start + 1;
      while (end < width && row[end].owner == start) end++;
      for (int i = start; i < end; i++) {
        row[i].text = " ";
        row[i].owner = -1;
      }
    }
    public void write(int x, int y, String text, String role, boolean focused, int extent) {
      if (y < 0 || y >= height || extent < 0)
        return;
      int limit = Math.min(width, x + extent);
      Style style = palette.style(role, focused);
      if (List.of("body", "hint", "info", "success", "warning", "error", "header").contains(role))
        style = new Style(style.foreground, palette.style("surface").background, style.bold,
            style.dim, style.underline);
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
      write(r.x, r.y, b[0] + b[4].repeat(r.width - 2) + b[1], role);
      write(r.x, r.y + r.height - 1, b[2] + b[4].repeat(r.width - 2) + b[3], role);
      for (int y = r.y + 1; y < r.y + r.height - 1; y++) {
        write(r.x, y, b[5], role);
        write(r.x + r.width - 1, y, b[5], role);
      }
      write(r.x + 2, r.y, clip(title, r.width - 4, false), role);
      return new Rect(r.x + 1, r.y + 1, r.width - 2, r.height - 2);
    }
    public void setCursor(int x, int y, int glyphWidth) {
      if (x >= 0 && x + Math.max(1, glyphWidth) <= width && y >= 0 && y < height) {
        cursorX = x;
        cursorY = y;
      } else
        cursorX = cursorY = -1;
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
}
