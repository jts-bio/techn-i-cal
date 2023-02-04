const list = document.querySelector("#slots");

let currentItem;
let currentIndex;

list.addEventListener("dragstart", function(event) {
  currentItem = event.target;
  currentIndex = Array.from(list.children).indexOf(currentItem);
});

list.addEventListener("dragover", function(event) {
  event.preventDefault();
  const targetIndex = Array.from(list.children).indexOf(event.target);
  if (targetIndex < 0) {
    return;
  }

  if (currentIndex < targetIndex) {
    list.insertBefore(currentItem, event.target.nextSibling);
  } else {
    list.insertBefore(currentItem, event.target);
  }
});

list.addEventListener("dragend", function() {
  currentItem = null;
});
