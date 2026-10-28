"""Exercise the actual offline H01-H07 browser export and import guards with Node."""
from pathlib import Path
import shutil
import subprocess
import unittest

RECORDER = Path(__file__).resolve().parents[2] / "docs/playtest/windows-h01-h07-offline.html"

NODE_HARNESS = r"""
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const html = fs.readFileSync(process.argv[1], "utf8");
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 1);
const elements = new Map();
let selectedStatus = "NOT_RUN", downloads = 0, copies = 0, latestBlob;
function element(id) {
  if (!elements.has(id)) {
    elements.set(id, {
      id, value: "", textContent: "", children: [], listeners: {}, focused: false,
      classList: {toggle() {}},
      addEventListener(type, handler) {this.listeners[type] = handler;},
      appendChild(child) {this.children.push(child);},
      setAttribute() {}, scrollIntoView() {}, focus() {this.focused = true;},
      click() {if (this.listeners.click) return this.listeners.click();},
      remove() {}
    });
  }
  return elements.get(id);
}
const document = {
  getElementById: element,
  createElement: tag => element("generated-" + tag + "-" + elements.size),
  body: {appendChild() {}},
  querySelector(selector) {
    if (selector === 'input[name="status"]:checked')
      return {value: selectedStatus};
    const m = /^input\[name="status"\]\[value="([^"]+)"\]$/.exec(selector);
    assert(m, "unexpected selector " + selector);
    return {
      set checked(value) {if (value) selectedStatus = m[1];},
      get checked() {return selectedStatus === m[1];}
    };
  }
};
const context = {
  document, console, Date, setTimeout() {},
  Blob: class {constructor(parts) {this.content = parts.join("");}},
  URL: {
    createObjectURL(blob) {downloads++; latestBlob = blob; return "blob:local";},
    revokeObjectURL() {}
  },
  navigator: {clipboard: {async writeText() {copies++;}}}
};
vm.runInNewContext(scripts[0][1], context, {filename: "offline-h01-h07.js"});
function click(id) {return element(id).listeners.click();}
async function importReport(record) {
  const payload = JSON.stringify(record);
  const target = {files: [{size: Buffer.byteLength(payload), async text() {return payload;}}], value: "report.json"};
  await element("file").listeners.change({target});
  return element("feedback").textContent;
}
(async () => {
  element("setup").value = "PC-A";
  element("platform").value = "physical_pc";
  element("hashCheck").value = "yes";
  click("save-json");
  assert.equal(downloads, 1);
  const original = JSON.parse(latestBlob.content);
  assert.equal(original.results.length, 7);
  assert.equal(original.official_release_gates_accepted_by_this_report, 0);
  element("evidence").value = "C:\\Users\\tester\\H01.png";
  click("save-json");
  click("save-md");
  await click("copy-md");
  assert.equal(downloads, 1, "path must block both download formats");
  assert.equal(copies, 0, "path must block clipboard export");
  assert.match(element("evidence-warning").textContent, /redacted filename/);
  assert.equal(element("evidence").focused, true);
  element("evidence").value = "H01-redacted.png";
  click("save-json");
  assert.equal(downloads, 2, "redacted basename must export");
  const valid = JSON.parse(latestBlob.content);
  assert.equal(valid.results[0].evidence, "H01-redacted.png");
  let tampered = structuredClone(valid);
  tampered.environment.setup = "x".repeat(33);
  assert.match(await importReport(tampered), /Invalid environment length or type: setup/);
  tampered = structuredClone(valid);
  tampered.environment.launcher = "x".repeat(91);
  assert.match(await importReport(tampered), /Invalid environment length or type: launcher/);
  tampered = structuredClone(valid);
  tampered.results[0].evidence = "../private/H01.png";
  assert.match(await importReport(tampered), /Invalid observed journey/);
  tampered = structuredClone(valid);
  tampered.environment.setup = "x".repeat(32);
  tampered.environment.launcher = "x".repeat(90);
  assert.match(await importReport(tampered), /Matching report imported/);
  click("save-json");
  assert.equal(downloads, 3);
  const resumed = JSON.parse(latestBlob.content);
  assert.equal(resumed.environment.setup.length, 32);
  assert.equal(resumed.environment.launcher.length, 90);
  assert.equal(resumed.results[0].evidence, "H01-redacted.png");
  assert.equal(resumed.complete_usa_events_accepted_by_this_report, 0);
  console.log("PASS: export path refusal, import limits, valid resume and zero-credit");
})().catch(error => {console.error(error); process.exitCode = 1;});
"""


class OfflineWindowsRecorderExportGuardTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_actual_embedded_browser_script_guards_export_and_resume(self):
        result = subprocess.run(
            [shutil.which("node"), "-e", NODE_HARNESS, str(RECORDER)],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: export path refusal", result.stdout)


if __name__ == "__main__":
    unittest.main()
