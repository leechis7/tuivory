package io.tuivory;
import static io.tuivory.Tuivory.*;

import java.util.List;
public final class ComponentsTest {
  private static void check(boolean value) {
    if (!value)
      throw new AssertionError();
  }
  public static void main(String[] args) {
    var tree = new Tree(List.of(new Node("r", "Root"), new Node("g", "Group", "r"),
        new Node("a", "한글 👩‍💻", "g"), new Node("z", "Other")));
    check(tree.handle("right", 3).kind().equals("expand"));
    check(tree.handle("down", 3).id().equals("g"));
    check(tree.handle("right", 3).kind().equals("expand"));
    check(tree.handle("right", 3).id().equals("a"));
    check(tree.handle("left", 3).id().equals("g"));
    check(tree.handle("left", 3).kind().equals("collapse"));
    check(cells("한글 👩‍💻") == 7);
    for (String theme : List.of("dark", "light", "blackwhite"))
      for (String colors : List.of("8", "16", "256", "truecolor")) {
        var c = new Canvas(20, 5, new Palette(theme, colors));
        c.write(0, 0, "한글💻abc", "body");
        var style = c.data[0][0].style;
        c.write(1, 0, " X", "selection", false, 2);
        check(c.data[0][0].text.equals(" "));
        check(c.data[0][0].style.background() == style.background());
        check(c.data[0][3].text.equals(" "));
        check(c.data[0][3].owner == -1);
        check(c.data[0][3].style.background() == style.background());
        var inner = c.panel(new Rect(0, 1, 20, 4), "Tuivory", true, false);
        tree.draw(c, inner, true, false);
        c.setCursor(3, 2, 2);
        check(!c.ansi().contains(" q"));
        check(!c.ansi().contains("\033[?12"));
        for (String line : c.lines()) check(cells(line) <= 20);
      }
    var state = new State();
    state.disabled = true;
    check(!state.editable());
    check(!state.activatable());
  }
}
