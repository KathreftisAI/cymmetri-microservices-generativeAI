const list1 = ["FirstName", "Display Name", "Email Address", "Id", "address"];
const list2 = ["fullname", "firstname", "company mail", "employeeId", "office address"];

const ul1 = document.getElementById("list1");
const ul2 = document.getElementById("list2");
const lines = document.getElementById("lines");

list1.forEach((item, index) => {
  const li = document.createElement("li");
  li.textContent = item;
  ul1.appendChild(li);

  const matchingIndex = list2.indexOf(item);
  if (matchingIndex !== -1) {
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", "0");
    line.setAttribute("y1", `${li.offsetTop + li.offsetHeight / 2}`);
    line.setAttribute("x2", "100%");
    line.setAttribute("y2", `${ul2.children[matchingIndex].offsetTop + ul2.children[matchingIndex].offsetHeight / 2}`);
    line.setAttribute("stroke", "#000");
    line.setAttribute("stroke-width", "2");
    lines.appendChild(line);
  }
});

list2.forEach((item, index) => {
  const li = document.createElement("li");
  li.textContent = item;
  ul2.appendChild(li);
});
