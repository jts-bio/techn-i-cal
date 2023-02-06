

var dragType = '';
var dragSource ;
var allowedTargets ;
var currentDropTarget;
// Employee: DRAGSTART
// 1:  amber highlights to turnarounds 
// 2: green highlights to slots

function employeeDragStart (event) {
    event.dataTransfer.setData('text', event.target.id);
    // add class hold to each slot
    document.querySelectorAll('.slot').forEach(slot => {
        if (event.target.dataset.available.split(" ").includes(slot.id)) {
            slot.classList.add('bg-green-400');
            // add to allowedTargets
            allowedTargets = event.target.dataset.available.split(" ");
        }
    })
    document.querySelectorAll('.slot.bg-green-400').forEach(slot => {
        if (event.target.dataset.turnarounds.split(" ").includes(slot.dataset.timeOfDay)) {
            slot.classList.add('bg-amber-400');
            // add a visible dropzone to the edge of the slots
        }
    })
    console.log('Slotted As', event.target.dataset.slottedAs);
    if (event.target.dataset.slottedAs  != "") {
        revealTrashbins();
        }
    }
function dragEnterSlot (event) {
    if (event.target.classList.contains('slot')) {
        if (event.target.dataset.available.split(" ").includes(event.dataTransfer.getData('text'))) {
            event.target.classList.add('ring','ring-green-300','ring-offset-2');
            currentDropTarget = event.target;
            console.log('currentDropTarget:', currentDropTarget.id);
        }
    }
}
function dragLeaveSlot (event) {
    if (event.target.classList.contains('slot')) {
        if (event.target.dataset.available.split(" ").includes(event.dataTransfer.getData('text'))) {
            event.target.classList.remove('ring','ring-green-300','ring-offset-2');
            currentDropTarget = null;
            console.log('currentDropTarget:',null);
        }
    }
}
document.querySelectorAll('.slot').forEach(slot => {
    slot.addEventListener('dragover', dragEnterSlot);
    slot.addEventListener('dragleave', dragLeaveSlot);
})
document.querySelectorAll('.fa-circle-ellipsis').forEach(slot => {
    slot.addEventListener('mouseover', mouseEnterEllipsis);
    slot.addEventListener('mouseleave', mouseLeaveEllipsis);
})
function dragFromSlot (event) {
    dragSource = 'slot';
}
function employeeDragEnd (event) {
    // remove class hold from all slots
    document.querySelectorAll('.slot').forEach(slot => {
        slot.classList.remove('bg-green-400','ring','ring-green-300','ring-offset-2','bg-amber-400');
    })
    // remove all dropzones
    document.querySelectorAll('.dropzone').forEach(dropzone => {
        dropzone.remove();
    })
}
function dragOverVerify (event) {
    if (event.target.classList.contains('slot')) {
        if (event.target.dataset.available.split(" ").includes(event.dataTransfer.getData('text'))) {
            event.preventDefault();
            event.target.classList.add('ring','ring-green-300','ring-offset-2');
        } else {
        }
    }
}
function dragOverTrash (event) {
    if (dragSource != 'slot') {} else {
        event.preventDefault();
    }
}
function dragEnterTrash (event) {
    event.target.classList.add('ring','ring-red-300','ring-offset-2','cursor-add');
    event.target.addEventListener("dragenter", function(event) {
        event.preventDefault();
        event.dataTransfer.dropEffect = "copy";
      });      
}
function dragLeaveTrash (event) {
    event.target.classList.remove('ring','ring-red-300','ring-offset-2');
}
function revealTrashbins (event) {
    document.querySelectorAll('.trashbin').forEach(trashbin => {
            trashbin.classList.remove('opacity-0');
    })
}
function hideTrashbins (event) {
    document.querySelectorAll('.trashbin').forEach(trashbin => {
        trashbin.classList.add('opacity-0');
    })
}
function dragLeave (event) {
    event.target.classList.remove('ring','ring-green-300','ring-offset-2');
}
function drop (event) {
    const data = event.dataTransfer.getData('text');
    const emplObj = document.getElementById(data);
    var availableFor = emplObj.dataset.available.split(" ");
    var allowContinue = false;

    availableFor.forEach(slot => {
        if (slot == event.target.id) {
            allowContinue = true;
        }
    });
    // return swapEmployee fx if dragging employee from slot to slot
    if (dragSource == 'slot') {
        swapEmployee(event, emplObj, allowContinue);
        return;
    }
    // Remove the employee from the previous slot if they were already in another slot
    const previousSlot = emplObj.parentElement;
    if (previousSlot && previousSlot != event.target) {
        previousSlot.removeChild(emplObj);
    }

    if (allowContinue) {
        event.target.appendChild(emplObj);
        // set animation on slot being updated
        event.target.classList.add('fa-fade');

        document.querySelectorAll('.slot').forEach(slot => {
            slot.classList.remove('bg-green-400','ring','ring-green-300','ring-offset-2');
        });

        // update the database
        const slot = event.target.id;
        const employee = event.dataTransfer.getData('text');
        const oldSlot = document.getElementById(employee).dataset.slottedAs;
        console.log(`${oldSlot},${oldSlotId}, ${slot}`);
        const url = `slot/${slot}/update/${employee}/`;

        const available = event.target.dataset.available.split(" ");
        if (available.includes(data)) {
            console.log('Available includes targetSlot');
            fetch(url)
                .then(response => response)
                .then(data => {
                    console.log(data);
                    // wait 750ms then reload the page
                    setTimeout(() => {
                        window.location.reload();
                    }, 750);
                });
        } else {
            alert ('PERMISSION DENIED: Employee would be placed in a turnaround.');
            window.location.reload();
        }
    }
}

function emplInSlotDragStart (event) {
    event.dataTransfer.setData('text', event.target.id);
    console.log(event.target.id);
    // select slots with event.target.id in data-available.split(" ")
    // add class hold to each slot
    document.querySelectorAll('.slot').forEach(slot => {
        if (slot.dataset.available.split(" ").includes(event.target.id)) {
            slot.classList.add('bg-green-400');
        }
    })
    document.querySelectorAll('.trashbin').forEach(trashbin => {
        trashbin.classList.remove('hidden');
    })
    dragType = 'inSlot';
}
function dragEnterTrash (event) {
}
function dragLeaveTrash (event) {
    event.target.classList.remove('bg-slate-600','ring','ring-red-300','ring-offset-2');
}
function backdropDragEnd (event) {
    event.target.classList.remove('bg-slate-600');
    dragType = '';
    document.querySelectorAll('.slot').forEach(slot => {
            slot.classList.remove('bg-green-400'); 
    })
}
function dropInTrash (event) {

    const data = event.dataTransfer.getData('text');
    const slot = document.getElementById(event.dataTransfer.getData('text')).parentNode;
    const shift = slot.children[0].innerText;
    

    if (dragSource == 'deck'){
    event.target.classList.remove('bg-slate-600');
    // remove the .employee from the .slot it originated from 
    
    slot.removeChild(document.getElementById(event.dataTransfer.getData('text')));
    slot.classList.add('fa-fade', 'fa-beat');
    // get data from drop
    
    // get .shift that is child of .slot element 
    
    console.log('Clearing Slot: ', shift)
    document.querySelectorAll('.slot').forEach(slot => {
        slot.classList.remove('bg-green-400','ring','ring-green-300','ring-offset-2');
    })
}
    const employee = data;
    const url = `slot/${shift}/delete/`;

    dragType = '';
    fetch(url)
        .then(response => response)
        .then(data => {
            console.log(data);
            // wait 750ms then reload the page
            setTimeout(() => {
                window.location.reload();
            }, 750);
        })
}
function getPopover (event, slotId) {
    // wait 1 second then fetch $slotId/popover/ 
    const url = `/wday/partial/${slotId}/slot-popover/`;
    fetch(url)
        .then(response => response.text())
        .then(data => {
            document.getElementById('popover-container-${slotId}').innerHTML = data;
        })
}

function mouseEnterEllipsis (event) {
    const slotId = event.target.dataset.slot;
    const slotGrp = event.target.dataset.group;
    console.log(slotId);
    // select .employee elements that have slotId in its dataset.shiftsAvailable 
    document.querySelectorAll('.employee-chip').forEach(employee => {
        if (employee.dataset.available.split(" ").includes(slotId)) {
            if (!employee.dataset.turnarounds.split(" ").includes(slotId)) {
            employee.classList.add('bg-green-400');
            employee.classList.add('scale-[115%]');
            }
        }
    })
}
function mouseLeaveEllipsis (event) {
    document.querySelectorAll('.employee').forEach(employee => {
        employee.classList.remove('bg-green-400');
        employee.classList.remove('scale-[115%]');
    })
}
function swapEmployees (event) {
    const slotA = event.target.dataset.slottedAs;
    const slotB = event.target.id;
    const empA = document.getElementById(slotA).dataset.slottedAs;
    const empB = document.getElementById(slotB).dataset.slottedAs;
    const url = `/wday/partial/${slotA}/swap/${slotB}/`;
    fetch(url)
        .then(response => response)
        .then(data => {
            console.log(data);
            // wait 750ms then reload the page
            setTimeout(() => {
                window.location.reload();
            }, 750);
        })
}
//get all .employee and fetch api/employee/<str:empPk>/checkPrevWd/<str:wdId>/
document.querySelectorAll('.employee').forEach(employee => {
    const wdId = document.getElementById('wdId').innerHTML;
    const empPk = employee.id;
    const url = `/sch/api/employee/${empPk}/checkPrevWd/${wdId}/`;
    fetch(url)
        .then(response => response.text())
        .then(data => {
            console.log(data);
            
            if (data =='PM' || data =='XN') {
                // remove .hidden from #ind-prev-pm
                document.getElementById(`${empPk}-ind-prev-pm`).classList.remove('hidden');
                employee.dataset.turnarounds += 'AM ';
            }
            if (data =='AM') {
                document.getElementById(`${empPk}-ind-prev-am`).classList.remove('hidden');
            }
        

        })
    })
document.querySelectorAll('.employee').forEach(employee => {
    const wdId = document.getElementById('wdId').innerHTML;
    const empPk = employee.id;
    const url = `/sch/api/employee/${empPk}/checkNextWd/${wdId}/`;
    fetch(url)
        .then(response => response.text())
        .then(data => {
            
            console.log(`${empPk}-ind-next-pm`);

            if (data =='PM' || data =='XN') {
                // remove .hidden from #ind-prev-pm
                document.getElementById(`${empPk}-ind-next-pm`).classList.remove('hidden');
                
            }
            if (data =='AM') {
                document.getElementById(`${empPk}-ind-next-am`).classList.remove('hidden');
                employee.dataset.turnarounds += 'PM ';
            }
        })
    })

