package io.tuivory.examples;
import static io.tuivory.Tuivory.*;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Standard-JVM line-input example. Hosts may connect their own raw terminal backend. */
public final class Catalog {
  public static void main(String[] args) throws IOException {
    String theme = "dark", colors = "256";
    boolean en = false, ascii = false, snapshot = false, ansiSnapshot = false;
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
          if (++i >= args.length || !args[i].equals("tree"))
            throw new IllegalArgumentException("Only --demo tree is supported");
        }
        case "--help" -> {
          System.out.println("--demo tree --lang ko|en --theme dark|light|blackwhite --colors "
              + "8|16|256|truecolor --ascii --snapshot");
          return;
        }
        default -> throw new IllegalArgumentException("unknown argument: " + args[i]);
      }
    }
    var tree = new Tree(List.of(new Node("root", en ? "Workspace" : "작업 공간"),
        new Node("src", en ? "Sources" : "소스", "root"),
        new Node("components", en ? "Components" : "컴포넌트", "src"),
        new Node("tree", en ? "Tree" : "트리", "components"),
        new Node("leaf", en ? "Fifth level" : "다섯 단계", "tree"),
        new Node("docs", en ? "Documentation" : "문서", "root")));
    tree.expanded.addAll(List.of("root", "src", "components", "tree"));
    var input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
    var output = new PrintWriter(new OutputStreamWriter(System.out, StandardCharsets.UTF_8), true);
    try {
      while (true) {
        var c = new Canvas(72, 18, new Palette(theme, colors));
        var area = c.panel(
            new Rect(0, 0, 72, 17), en ? "Tuivory Java example" : "Tuivory Java 예제", true, ascii);
        tree.draw(c, area, true, ascii);
        c.write(0, 17,
            en ? "Type up/down/left/right/activate/quit, then Enter"
               : "up/down/left/right/activate/quit 입력 후 Enter",
            "hint");
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
        tree.handle(line.strip(), area.height());
      }
    } finally {
      if (!snapshot) {
        output.print("\033[0m\033[?25h\n");
        output.flush();
      }
    }
  }
}
