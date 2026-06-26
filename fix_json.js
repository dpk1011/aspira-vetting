const fs = require("fs");
const path = require("path");

const targetDir = path.join(__dirname, "C9/MATHS");
const files = fs
  .readdirSync(targetDir)
  .filter((f) => f.toUpperCase().endsWith(".JSON"));

const isDryRun = process.argv.includes("--dry-run");
console.log(`Running in ${isDryRun ? "DRY-RUN" : "WRITE"} mode.\n`);

const fixJson = (str) => {
  return (
    str
      // 1. Double escape LaTeX commands starting with f, t, r, b
      .replace(/(?<!\\)((?:\\\\)*)\\([ftrb])/g, "$1\\\\$2")
      // 2. Explicitly escape LaTeX commands starting with 'n'
      .replace(
        /(?<!\\)((?:\\\\)*)\\(neq|nabla|nu|notin|nsubseteq|normalsize|not)/g,
        "$1\\\\$2",
      )
      // 3. Explicitly escape LaTeX commands starting with 'u'
      .replace(/(?<!\\)((?:\\\\)*)\\(up|under|uplus)/g, "$1\\\\$2")
      // 4. Safely escape everything else EXCEPT valid JSON escapes (", \, /, n, u)
      .replace(/(?<!\\)((?:\\\\)*)\\([^"\\/nu])/g, "$1\\\\$2")
  );
};

let totalFixed = 0;
let totalFailed = 0;

for (const file of files) {
  const filePath = path.join(targetDir, file);
  const rawContent = fs.readFileSync(filePath, "utf8");

  const fixedContent = fixJson(rawContent);

  if (rawContent !== fixedContent) {
    console.log(`\n📄 File: ${file}`);

    // Find lines that changed for logging
    const rawLines = rawContent.split("\n");
    const fixedLines = fixedContent.split("\n");
    let fileDiffs = 0;

    for (let i = 0; i < rawLines.length; i++) {
      if (rawLines[i] !== fixedLines[i]) {
        if (fileDiffs < 3 || !isDryRun) {
          console.log(`  Line ${i + 1}:`);
          console.log(`  - ${rawLines[i].trim()}`);
          console.log(`  + ${fixedLines[i].trim()}`);
        }
        fileDiffs++;
      }
    }
    if (fileDiffs > 3 && isDryRun) {
      console.log(`  ... and ${fileDiffs - 3} more changes in this file.`);
    }

    try {
      JSON.parse(fixedContent);
      console.log(`  ✅ Successfully verified JSON parse of fixed content.`);
      if (!isDryRun) {
        fs.writeFileSync(filePath, fixedContent, "utf8");
        console.log(`  💾 Saved changes.`);
      }
      totalFixed++;
    } catch (e) {
      console.log(`  ❌ Error parsing fixed JSON: ${e.message}`);
      totalFailed++;
    }
  } else {
    // Check if it's already valid
    try {
      JSON.parse(rawContent);
    } catch (e) {
      console.log(`\n📄 File: ${file} - UNCHANGED but INVALID: ${e.message}`);
    }
  }
}

console.log(`\n--- Summary ---`);
console.log(`Modified and Passed: ${totalFixed}`);
console.log(`Failed Parsing: ${totalFailed}`);
if (isDryRun) {
  console.log(
    `\n(Dry-Run Complete. No files were modified. Run without --dry-run to apply changes.)`,
  );
}
