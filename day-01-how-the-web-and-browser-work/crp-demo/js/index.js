// Turns the heading green, and reports what the parser had built when this script ran.
const heading = document.querySelector("h1");
if (heading) heading.style.color = "green";

console.log(
  `[${Math.round(performance.now())} ms] index.js ran.`,
  "Paragraph after the scripts exists yet?",
  document.getElementById("after") !== null
);
