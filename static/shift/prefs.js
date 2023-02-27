const scoreColumns = document.querySelectorAll('.score-column');
const employees = document.querySelectorAll('.employee');

// employees are draggable nodes 
employees.forEach(employee => {
  employee.addEventListener('dragstart', dragStart);
  employee.addEventListener('dragend', dragEnd);
});

function dragStart() {
  this.classList.add('dragging');
  var name = this.getAttribute('data-employee');
  var score = this.getAttribute('data-score');
  // set the request header 'employee' and 'score' to the employee name and score
  this.setAttribute('employee', name);
  console.log('dragStart', name, score);
}

// scoreColumns are the drop targets
scoreColumns.forEach(scoreColumn => {
  scoreColumn.addEventListener('dragover', dragOver);
  scoreColumn.addEventListener('dragenter', dragEnter);
  scoreColumn.addEventListener('dragleave', dragLeave);
  scoreColumn.addEventListener('drop', dragDrop);
});

  function dragOver(e) {
    e.preventDefault();
    this.style.backgroundColor = '#f0f0f022';
  };


  function dragLeave(e) {
    this.style.backgroundColor = '';
  }

  function dragDrop(e) {
    e.preventDefault();
    this.style.backgroundColor = '';
    const employee = document.querySelector('.dragging');
    this.appendChild(employee);
    employee.classList.remove('dragging');
  }

  function dragEnter(e) { 
    e.preventDefault();
    this.style.backgroundColor = '#f0f0f022';
  }

  function dragEnd() {
    this.classList.remove('dragging');
  }

