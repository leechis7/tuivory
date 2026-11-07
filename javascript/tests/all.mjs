import "./components.mjs";
import "./workspace.mjs";

import "./text.mjs";

import "./forms.mjs";

import "./focus.mjs";

import "./collections.mjs";

import "./menu.mjs";
import "./feedback.mjs";
import "./layout.mjs";

import "./canvas-copy.mjs";

import "./containers.mjs";

import "./surfaces.mjs";

import "./popups.mjs";

import "./dialogs.mjs";

import test from "node:test";

test("document, syntax, grid and drag shared regressions", async () => {
  await import("./documents.mjs");
  await import("./syntax.mjs");
  await import("./grid.mjs");
  await import("./grid-pointer.mjs");
  await import("./drag.mjs");
  await import("./terminal.mjs");
});
