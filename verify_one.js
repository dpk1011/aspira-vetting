const fs = require('fs');
const path = require('path');

const targetDir = path.join(__dirname, 'C6/MATHS');
const file = 'C01.JSON';
const filePath = path.join(targetDir, file);
const rawContent = fs.readFileSync(filePath, 'utf8');

const fixJson = (str) => {
  return str
    .replace(/(?<!\\)\\([ftrb])/g, '\\\\$1')
    .replace(/(?<!\\)\\(neq|nabla|nu|notin|nsubseteq|normalsize|not)/g, '\\\\$1')
    .replace(/(?<!\\)\\(up|under|uplus)/g, '\\\\$1')
    .replace(/(?<!\\)\\([^"\\/nu])/g, '\\\\$1');
};

const fixedContent = fixJson(rawContent);

try {
  const parsed = JSON.parse(fixedContent);
  console.log(`Successfully parsed ${file}. Here is a preview of the first card:\n`);
  console.log(JSON.stringify(parsed.cards[0], null, 2));
} catch (e) {
  console.log(`Failed to parse: ${e.message}`);
}
