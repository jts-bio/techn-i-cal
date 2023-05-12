



// Use Notes:
// Give all slots the class .slot-container
// 



const slotContainers = document.getElementsByClassName("slot-container");
const onDeckContainer = document.getElementById("on-deck-container");
const scheduledOffContainer = document.getElementById("scheduled-off-container");
const shiftSlots = document.getElementsByClassName("slot");


// EVENT LISTENERS 
    // --DRAGSTART
  onDeckContainer.addEventListener("dragstart", dragStart);
  scheduledOffContainer.addEventListener("dragstart", dragStart);
  for (let i = 0; i < shiftSlots.length; i++) {
    shiftSlots[i].addEventListener("dragstart", dragStart);
  }
  
    // --DRAGOVER
  for (let i = 0; i < slotContainers.length; i++) {
    slotContainers[i].addEventListener("dragover", dragOver);
  }

    // --DRAGLEAVE
  for (let i = 0; i < slotContainers.length; i++) {
    slotContainers[i].addEventListener("dragleave", dragLeave);
  }
  
    // --DROP
    for (let i = 0; i < slotContainers.length; i++) {
    slotContainers[i].addEventListener("drop", drop);
    }

    // --DRAGEND
    onDeckContainer.addEventListener("dragend", dragEnd);   
    scheduledOffContainer.addEventListener("dragend", dragEnd);
    for (let i = 0; i < shiftSlots.length; i++) {
        shiftSlots[i].addEventListener("dragend", dragEnd);
    }

  
  function dragStart(event) {
    // Get the id of the employee that is being dragged
    const employeeId = event.target.id;
    event.dataTransfer.setData("text", employeeId);
    console.log("dragStart", employeeId);
    // Highlight all the slot-containers that the employee IS TRAINED FOR, 
    // which is indicated by fb-<empId> in the class list of the slot-container
    const slots = document.querySelectorAll(".slot-container");
    for (const slot of slots) {
      if (slot.classList.contains("fb-" + employeeId)) {
        slot.style.background = "rgba(255, 255, 255, 0.2)";
      }
    }
  }
  
  function dragOver(event) {
    event.preventDefault();
    // if the employee being held matches the target by class fb-<empId> 
    // then highlight the target even brighter
    const employeeId = event.dataTransfer.getData("text");
    const slot = event.target;
    if (slot.classList.contains("fb-" + employeeId)) {
        slot.style.background = "#ffffff66";
        }
    
  }

  function dragLeave(event) {
    event.preventDefault();
    event.target.style.background = "";
  }
  
  function dragEnd (event) {
    // Remove the highlight from all the slot-containers
    const slots = document.querySelectorAll(".slot-container");
    for (const slot of slots) {
      slot.style.background = "rgba(255, 255, 255, 0.0)";
    }
  }

  function drop (event) {
    // Prevent the default drop action
    event.preventDefault();
    // Get the id of the employee that is being dropped
    const employeeId = event.dataTransfer.getData("text");
    const shiftId = event.target.getAttribute("id");
    console.log("drop", employeeId);
    console.log("into" ,shiftId);
    // if the employee being held matches the target by class fb-<empId> 
      // then drop the employee into the target
      console.log('fb-${employeeId}');
      if (event.target.classList.contains("fb-" + employeeId)) {
          event.target.appendChild(document.getElementById(employeeId
          ));
          console.log("dropped", employeeId, "into", shiftId);
      };

  };