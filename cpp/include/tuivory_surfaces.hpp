#pragma once
namespace tuivory {
struct Surface {
  std::string role = "surface";
  void draw(Canvas &canvas, Rect bounds,
            const std::function<void(Canvas &)> &painter) const {
    for (int v : {bounds.x, bounds.y, bounds.width, bounds.height})
      container_detail::number(v);
    Canvas child(bounds.width, bounds.height, canvas.palette, role);
    painter(child);
    canvas.blit(child, {0, 0, bounds.width, bounds.height}, bounds.x, bounds.y);
  }
};
} // namespace tuivory
