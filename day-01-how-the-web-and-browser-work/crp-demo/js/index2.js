// Adds a line to the heading, and reports the same thing as index.js.
const title = document.querySelector("h1");
if (title) title.textContent += " + index2.js ran";

console.log(
  `[${Math.round(performance.now())} ms] index2.js ran.`,
  "Paragraph after the scripts exists yet?",
  document.getElementById("after") !== null
);
