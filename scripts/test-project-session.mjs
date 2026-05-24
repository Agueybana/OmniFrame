import assert from "node:assert/strict";
import { deriveProjectTitle, parseCookieValue, PROJECT_COOKIE_NAME } from "../src/lib/projectSession.js";

assert.equal(deriveProjectTitle("Launch AI roadmap\nwith focus on adoption"), "Launch AI roadmap");
assert.equal(deriveProjectTitle(""), "Untitled analysis");
assert.equal(parseCookieValue("a=1; omniframe_project_id=abc-123; b=2", PROJECT_COOKIE_NAME), "abc-123");
assert.equal(parseCookieValue("", PROJECT_COOKIE_NAME), null);

console.log("projectSession tests passed");
