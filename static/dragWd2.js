
var currentEmployee = document.getElementById("current-employee");
var currentAllowedDrops = document.getElementById("current-allowed-drops");
var currentDropzone = document.getElementById("current-dropzone");
var isCurDropAllowed = document.getElementById("is-drop-allowed");
currentEmployee.innerHTML = "No employee selected";
currentAllowedDrops.innerHTML = "...";

document.querySelectorAll(".employee-chip").forEach(function (chip) {
  chip.addEventListener("dragstart", dragStartChip);
  chip.addEventListener("dragend", dragEndChip);
});

function dragStartChip(event) {
  var allowedSlotIds = event.target.dataset.available.split(" ");
  var slots = document.querySelectorAll(".slot");
  slots.forEach(function (slot) {
    if (allowedSlotIds.includes(slot.id)) {
      slot.classList.add("allowed-drop", "bg-emerald-400");
    }
    document.querySelectorAll(".allowed-drop").forEach(function (slot) {
        slot.addEventListener("dragover", dragOverVerify);
        slot.addEventListener("drop", drop);
    })
  });

  currentEmployee.innerHTML = event.target.id;
  currentAllowedDrops.innerHTML = event.target.dataset.available;
  event.dataTransfer.setData("text/plain", event.target.id);
  event.dataTransfer.dropEffect = "move";
  event.target.classList.add("dragging");
}

function dragEndChip(event) {
  currentEmployee.innerHTML = "No employee selected";
  currentAllowedDrops.innerHTML = "...";
  event.target.classList.remove("dragging");
  var slots = document.querySelectorAll(".slot");
  slots.forEach(function (slot) {
    slot.classList.remove(
      "over-allowed-drop",
      "bg-emerald-400",
      "allowed-drop",
      "over-prohibited-drop",
      "bg-orange-400"
    );
  });
}

document.querySelectorAll(".slot").forEach(function (slot) {
  
  slot.addEventListener("drop", drop)
  slot.addEventListener("dragover", dragOverVerify);
});

        function dragOverVerify(event) {
        event.stopPropagation();
        var allowedSlotIds = event.target.dataset.available.split(" ");
        currentDropzone.innerHTML = event.target.id;
        if (allowedSlotIds.includes(event.target.id)) {
            event.preventDefault();
            event.dataTransfer.dropEffect = "move";
        } else {
        if (currentAllowedDrops.innerHTML.split(" ").includes(event.target.id)) {
            isCurDropAllowed.innerHTML = "ALLOWED";
            event.target.classList.add("bg-emerald-300");
        } else {
            isCurDropAllowed.innerHTML = "PROHIBITED";
            event.target.classList.add('bg-orange-300');
        }
    }}
          function dragLeave (event) {
            isCurDropAllowed.innerHTML = '...';
            currentDropzone.innerHTML = '...';
            event.target.classList.remove('hover:over-allowed-drop','over-allowed-drop','bg-emerald-300','over-prohibited-drop','bg-orange-300');
          }
          function dragEnd (event) {
            isCurDropAllowed.innerHTML = '...';
            currentEmployee.innerHTML = 'No employee selected';
            currentDropzone.innerHTML = '...';
            currentAllowedDrops.innerHTML = '...';
            event.target.classList.remove('allowed-drop','bg-emerald-400','over-allowed-drop','bg-emerald-400','over-prohibited-drop','bg-orange-400');
          }
          function drop (event) {
            var currentEmployeeChip;
            if (isCurDropAllowed.innerHTML == 'ALLOWED') {
                event.preventDefault();
                event.dataTransfer.dropEffect = 'move';
                var data = event.dataTransfer.getData('text/plain');
                event.target.appendChild(document.getElementById(data));
                
            } else {
                event.dataTransfer.dropEffect = 'none';
                console.log('not ok'); 
            }
            event.target.classList.remove('over-allowed-drop','bg-emerald-300','over-prohibited-drop','bg-orange-300','allowed-drop','bg-emerald-400');
            currentEmployeeChip = event.target.querySelector('.employee-chip');
            console.log(currentEmployeeChip);
            event.preventDefault();
            event.dataTransfer.dropEffect = 'move';
            var data = event.dataTransfer.getData('text/plain');
            event.target.appendChild(document.getElementById(data));
          }
          
        document.querySelectorAll('.slot').forEach(function (slot) {
            slot.addEventListener('dragover', dragOverVerify);
            slot.addEventListener('drop', drop);
            slot.addEventListener('dragleave', dragLeave);
        });