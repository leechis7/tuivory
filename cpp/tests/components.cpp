#include "tuivory.hpp"
#include <cassert>
int main() {
  using namespace tuivory;
  Tree tree({{"r", "Root"},
             {"g", "Group", "r"},
             {"a", "한글 👩‍💻", "g"},
             {"z", "Other"}});
  assert(tree.handle("right", 3).kind == "expand");
  assert(tree.handle("down", 3).id == "g");
  assert(tree.handle("right", 3).kind == "expand");
  assert(tree.handle("right", 3).id == "a");
  assert(tree.handle("left", 3).id == "g");
  assert(tree.handle("left", 3).kind == "collapse");
  assert(cells("한글 👩‍💻") == 7);
  for (const auto &bad : {"\xf8\x90\x80\x80", "\xc0\xaf", "\xed\xa0\x80",
                          "\xf4\x90\x80\x80", "\xe2\x82"}) {
    bool rejected = false;
    try {
      (void)cells(bad);
    } catch (const std::invalid_argument &) {
      rejected = true;
    }
    assert(rejected);
  }
  for (const auto &theme : {"dark", "light", "blackwhite"})
    for (const auto &colors : {"8", "16", "256", "truecolor"}) {
      Canvas c(20, 5, Palette(theme, colors));
      c.write(0, 0, "한글💻abc");
      auto style = c.data[0][0].style;
      c.write(1, 0, " X", "selection", false, 2);
      assert(c.data[0][0].text == " ");
      assert(c.data[0][0].style.background == style.background);
      assert(c.data[0][3].text == " ");
      assert(c.data[0][3].owner == -1);
      assert(c.data[0][3].style.background == style.background);
      auto inner = c.panel({0, 1, 20, 4}, "Tuivory", true);
      tree.draw(c, inner);
      c.set_cursor(3, 2);
      const auto ansi = c.ansi();
      assert(ansi.find(" q") == std::string::npos);
      assert(ansi.find("\033[?12") == std::string::npos);
      for (const auto &line : c.lines())
        assert(cells(line) <= 20);
    }
  State s;
  s.disabled = true;
  assert(!s.editable());
  assert(!s.activatable());
}
