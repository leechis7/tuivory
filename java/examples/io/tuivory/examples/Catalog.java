package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Standard-JVM line-input example. Hosts may connect their own raw terminal backend. */
public final class Catalog {
  private static void workspaceDraw(Tree tree, Tabs tabs, Split split, Canvas canvas, Rect area,
      boolean tabFocus, boolean en, boolean ascii) {
    tabs.draw(canvas, new Rect(area.x(), area.y(), area.width(), 1), tabFocus, ascii);
    breadcrumbs(List.of(new PathItem("root", en ? "Workspace" : "작업 공간"),
                    new PathItem("current", en ? "Components" : "컴포넌트")),
        area.width())
        .draw(canvas, new Rect(area.x(), area.y() + 1, area.width(), 1));
    int body = Math.max(0, area.height() - 3);
    var layout = split.layout(area.width());
    Rect right = new Rect(area.x(), area.y() + 2, area.width(), body);
    if (!layout.compact()) {
      var left = canvas.panel(new Rect(area.x(), area.y() + 2, layout.first(), body),
          en ? "Explorer" : "탐색", !tabFocus, ascii);
      tree.draw(canvas, left, !tabFocus, ascii);
      for (int y = 0; y < body; y++)
        canvas.write(
            area.x() + layout.first(), area.y() + 2 + y, ascii ? "|" : "│", "focus.border");
      right = new Rect(area.x() + layout.first() + 1, area.y() + 2, layout.second(), body);
    }
    right = canvas.panel(right, en ? "Content" : "내용", false, ascii);
    canvas.write(
        right.x(), right.y(), en ? "Selected tab" : "선택한 탭", "hint", false, right.width());
    canvas.write(right.x(), right.y() + 1,
        (tabs.active.equals("draft") ? (en ? "Draft" : "초안") : (en ? "Overview" : "개요")),
        "body", false, right.width());
    statusLine(List.of(new StatusItem("ready", en ? "Ready" : "준비", "success", 10),
                   new StatusItem(
                       "keys", en ? "tab focus | < > resize" : "tab 포커스 | < > 크기", "hint", 1)),
        area.width())
        .draw(canvas, new Rect(area.x(), area.y() + area.height() - 1, area.width(), 1));
  }

  public static void main(String[] args) throws IOException {
    String theme = "dark", colors = "256";
    boolean en = false, ascii = false, snapshot = false, ansiSnapshot = false, workspace = false,
            tabFocus = false, textDemo = false, formDemo = false, listDemo = false,
            pickerDemo = false, menuDemo = false, contextDemo = false, feedbackDemo = false,
            layoutDemo = false, containerDemo = false, surfaceDemo = false, shadowDemo = false,
            dialogDemo = false, documentDemo = false, syntaxDemo = false;
    for (int i = 0; i < args.length; i++) {
      switch (args[i]) {
        case "--lang" -> {
          if (++i >= args.length)
            throw new IllegalArgumentException("missing language");
          en = args[i].equals("en");
        }
        case "--theme" -> {
          if (++i >= args.length)
            throw new IllegalArgumentException("missing theme");
          theme = args[i];
        }
        case "--colors" -> {
          if (++i >= args.length)
            throw new IllegalArgumentException("missing profile");
          colors = args[i];
        }
        case "--ascii" -> ascii = true;
        case "--snapshot" -> snapshot = true;
        case "--snapshot-ansi" -> {
          snapshot = true;
          ansiSnapshot = true;
        }
        case "--demo" -> {
          if (++i >= args.length)
            throw new IllegalArgumentException("missing demo");
          workspace = args[i].equals("workspace");
          textDemo = args[i].equals("text");
          formDemo = args[i].equals("form");
          listDemo = args[i].equals("list");
          pickerDemo = args[i].equals("picker");
          contextDemo = args[i].equals("context-menu");
          feedbackDemo = args[i].equals("feedback");
          layoutDemo = args[i].equals("layout");
          containerDemo = args[i].equals("container");
          surfaceDemo = args[i].equals("surface");
          shadowDemo = args[i].equals("shadow");
          dialogDemo = args[i].equals("dialog");
          syntaxDemo = args[i].equals("syntax");
          documentDemo = args[i].equals("document") || syntaxDemo;
          if (shadowDemo)
            menuDemo = contextDemo = true;
          menuDemo = contextDemo || args[i].equals("menu");
          if (!args[i].equals("tree") && !workspace && !textDemo && !formDemo && !listDemo
              && !pickerDemo && !menuDemo && !feedbackDemo && !layoutDemo && !containerDemo
              && !surfaceDemo && !dialogDemo && !documentDemo)
            throw new IllegalArgumentException("Supported demos: tree, workspace, text, form, "
                + "list, picker, menu, context-menu, feedback");
        }
        case "--help" -> {
          System.out.println("--demo "
              + "tree|workspace|text|form|list|picker|menu|context-menu|feedback|layout|container|"
              + "surface|shadow|dialog|document|syntax "
              + "--lang ko|en "
              + "--theme "
              + "dark|light|blackwhite --colors "
              + "8|16|256|truecolor --ascii --snapshot");
          return;
        }
        default -> throw new IllegalArgumentException("unknown argument: " + args[i]);
      }
    }
    var menuHost = new MenuHost(en, contextDemo, shadowDemo);
    var feedbackHost = new FeedbackHost(en);
    var layoutHost = new LayoutHost(en);
    var containerHost = new ContainerHost(en, ascii);
    var documentHost = new DocumentHost(en, ascii, syntaxDemo);
    var dialogHost = new DialogHost(en);
    var surfaceHost = new SurfaceHost(en);
    var tree = new Tree(List.of(new Node("root", en ? "Workspace" : "작업 공간"),
        new Node("src", en ? "Sources" : "소스", "root"),
        new Node("components", en ? "Components" : "컴포넌트", "src"),
        new Node("tree", en ? "Tree" : "트리", "components"),
        new Node("leaf", en ? "Fifth level" : "다섯 단계", "tree"),
        new Node("docs", en ? "Documentation" : "문서", "root")));
    tree.expanded.addAll(List.of("root", "src", "components", "tree"));
    var draft = new Tab("draft", en ? "Draft document" : "초안 문서");
    draft.edited = true;
    draft.closable = true;
    var disabled = new Tab("disabled", en ? "Disabled" : "비활성");
    disabled.disabled = true;
    var tabs = new Tabs(List.of(new Tab("overview", en ? "Overview" : "개요"), draft, disabled));
    var split = new Split(16, 20, 24);
    var text = new Text(en ? (ascii ? "Grapheme text\nEdit with real cursor."
                                    : "Unicode é 界\nEdit with real cursor.")
                           : "한글 é 界\n여러 줄을 편집합니다.");
    var name = new Field("name", "text");
    name.label = en ? "Name" : "이름";
    name.value = en ? "Input" : "한글 입력";
    name.required = true;
    var password = new Field("password", "password");
    password.label = en ? "Password" : "비밀번호";
    password.value = "example";
    var off = new Field("off", "checkbox");
    off.label = en ? "Disabled" : "비활성";
    off.state.disabled = true;
    var mode = new Field("mode", "select");
    mode.label = en ? "Mode" : "모드";
    mode.choice = "a";
    mode.options = List.of(new FormOption("a", en ? "Default" : "기본"),
        new FormOption("off", en ? "Unavailable" : "사용 불가", true),
        new FormOption("b", en ? "Alternative" : "다른 값"));
    var apply = new Field("apply", "button");
    apply.label = en ? "Apply" : "적용";
    apply.action = "submit";
    var form = new Form(List.of(name, password, off, mode, apply));
    var group = new Item("group", en ? "Languages" : "지원 언어");
    group.separator = true;
    var go = new Item("go", "Go");
    go.secondary = en ? "Static package" : "정적 패키지";
    go.icon = "◆";
    go.asciiIcon = "G";
    go.shortcut = "G";
    var inactive = new Item("off", en ? "Disabled" : "비활성");
    inactive.disabled = true;
    var rs = new Item("rust", "Rust");
    rs.secondary = en ? "Independent implementation" : "독립 구현";
    rs.icon = "◆";
    rs.asciiIcon = "R";
    rs.shortcut = "R";
    var doc = new Item("docs", en ? "Documentation" : "문서");
    doc.secondary = en ? "Korean and English" : "한글·영어";
    doc.icon = "◇";
    doc.asciiIcon = "D";
    var collectionItems = List.of(group, go, inactive, rs, doc);
    var list = new ListModel(collectionItems);
    var picker = new SearchPicker(collectionItems);
    picker.handle("open");
    list.empty = picker.list.empty = en ? "(empty)" : "항목 없음";
    var input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
    var output = new PrintWriter(new OutputStreamWriter(System.out, StandardCharsets.UTF_8), true);
    try {
      while (true) {
        var c = new Canvas(72, 18, new Palette(theme, colors));
        var area = c.panel(
            new Rect(0, 0, 72, 17), en ? "Tuivory Java example" : "Tuivory Java 예제", true, ascii);
        if (documentDemo)
          documentHost.draw(c, area, ascii);
        else if (dialogDemo)
          dialogHost.draw(c, area, ascii);
        else if (surfaceDemo)
          surfaceHost.draw(c, area, ascii);
        else if (containerDemo)
          containerHost.draw(c, area, ascii);
        else if (layoutDemo)
          layoutHost.draw(c, area, ascii);
        else if (feedbackDemo)
          feedbackHost.draw(c, area, ascii);
        else if (menuDemo)
          menuHost.draw(c, area, ascii);
        else if (listDemo)
          list.draw(c, area, true, ascii);
        else if (pickerDemo)
          picker.draw(c, area, true, ascii);
        else if (formDemo)
          form.draw(c, area, true);
        else if (textDemo)
          text.draw(c, area, true);
        else if (workspace)
          workspaceDraw(tree, tabs, split, c, area, tabFocus, en, ascii);
        else
          tree.draw(c, area, true, ascii);
        String hint = surfaceDemo ? (en ? "Type s / quit, then Enter" : "s / quit 입력 후 Enter")
            : containerDemo       ? (en ? "Type m / l / h / next / click x y / quit, then Enter"
                                        : "m / l / h / next / click x y / quit 입력 후 Enter")
            : layoutDemo          ? (en ? "Type x / activate / d / click x y / quit, then Enter"
                                        : "x / activate / d / click x y / quit 입력 후 Enter")
            : feedbackDemo        ? (en ? "Type activate / delete / t / c / quit, then Enter"
                                        : "activate / delete / t / c / quit 입력 후 Enter")
            : menuDemo            ? (en ? "Type f10 / down / activate / cancel / quit, then Enter"
                                        : "f10 / down / activate / cancel / quit 입력 후 Enter")
            : pickerDemo          ? (en ? "Type insert text / activate / cancel / quit, then Enter"
                                        : "insert 검색어 / activate / cancel / quit 입력 후 Enter")
            : formDemo            ? (en ? "Type insert text / tab / activate / quit, then Enter"
                                        : "insert 값 / tab / activate / quit 입력 후 Enter")
            : textDemo            ? (en ? "Type insert text / home / backspace / quit, then Enter"
                                        : "insert 값 / home / backspace / quit 입력 후 Enter")
            : en                  ? "Type up/down/left/right/activate/quit, then Enter"
                                  : "up/down/left/right/activate/quit 입력 후 Enter";
        c.write(0, 17, hint, "hint");
        if (snapshot) {
          if (ansiSnapshot) {
            output.print(c.ansi());
            output.flush();
          } else
            for (String line : c.lines()) output.println(line);
          return;
        }
        output.print(c.ansi() + "\033[19;1H\033[K> \033[?25h");
        output.flush();
        String line = input.readLine();
        if (line == null || line.equals("quit"))
          break;
        String action = line.strip();
        if (textDemo || formDemo || listDemo || pickerDemo || menuDemo || feedbackDemo || layoutDemo
            || containerDemo || surfaceDemo || dialogDemo || documentDemo) {
          int space = action.indexOf(' ');
          String command = space < 0 ? action : action.substring(0, space);
          String addition = space < 0 ? "" : action.substring(space + 1);
          if (documentDemo)
            documentHost.handle(command, addition);
          else if (dialogDemo)
            dialogHost.handle(command, addition);
          else if (surfaceDemo)
            surfaceHost.handle(command, addition);
          else if (containerDemo)
            containerHost.handle(command, addition);
          else if (layoutDemo)
            layoutHost.handle(command, addition);
          else if (feedbackDemo)
            feedbackHost.handle(command, addition);
          else if (menuDemo)
            menuHost.handle(command, addition);
          else if (listDemo)
            list.handle(command, area.height());
          else if (pickerDemo)
            picker.handle(command, addition, area.height());
          else if (formDemo)
            form.handle(command.equals("tab") ? "next" : command, addition);
          else
            text.handle(command, addition);
        } else if (workspace && action.equals("tab"))
          tabFocus = !tabFocus;
        else if (workspace && (action.equals("<") || action.equals(">")))
          split.resize(area.width(), split.preferred + (action.equals("<") ? -1 : 1));
        else if (workspace && tabFocus)
          tabs.handle(action.equals("left") ? "previous"
                  : action.equals("right")  ? "next"
                                            : action);
        else
          tree.handle(action, area.height());
      }
    } finally {
      if (!snapshot) {
        output.print("\033[0m\033[?25h\n");
        output.flush();
      }
    }
  }
}
