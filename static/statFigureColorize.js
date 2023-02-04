(function() {
  var colorizeFigure;

  colorizeFigure = function(figName, goals) {
    var figure, n;
    figure = document.getElementById(figName);
    // figure as number 
    n = parseInt(figure.innerHTML);
    console.log(figure);
    // on mutation of figure, run the following function
    return figure.addEventListener("DOMSubtreeModified", function() {
      var direction, fair_boundary, good_boundary, great_boundary;
      // clear all classes
      figure.classList.remove("bg-green-500");
      figure.classList.remove("bg-yellow-500");
      figure.classList.remove("bg-red-500");
      // goals as array 
      great_boundary = goals[0];
      good_boundary = goals[1];
      fair_boundary = goals[2];
      if (great_boundary > fair_boundary) {
        direction = -1;
      }
      if (great_boundary < fair_boundary) {
        direction = 1;
      }
      if (direction = 1) {
        console.log("FORWARD DIRECTION DETECTED");
        if (n > great_boundary) {
          figure.classList.add("bg-green-500");
        }
        if (n.innerHTML > good_boundary) {
          figure.classList.add("bg-yellow-500");
        }
        if (n.innerHTML > fair_boundary) {
          figure.classList.add("bg-red-500");
        }
      }
      if (direction = -1) {
        console.log("REVERSE DIRECTION DETECTED");
        if (n.innerHTML < great_boundary) {
          figure.classList.add("bg-green-500");
        }
        if (n.innerHTML < good_boundary) {
          figure.classList.add("bg-yellow-500");
        }
        if (n.innerHTML < fair_boundary) {
          return figure.classList.add("bg-red-500");
        }
      }
    });
  };

}).call(this);


//# sourceMappingURL=statFigureColorize.js.map
//# sourceURL=coffeescript