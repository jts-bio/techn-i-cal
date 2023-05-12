(function() {
  var dropArea, dropAreaColor, dropAreaHoverColor, isDropped, item1, item1OriginX, item1OriginY, mainScreen, mainScreenHeight, mainScreenWidth, undoButton;

  mainScreenWidth = 400;

  mainScreenHeight = 300;

  isDropped = false;

  mainScreen = new Layer({
    backgroundColor: "#ffffff",
    width: mainScreenWidth,
    height: mainScreenHeight,
    y: 16,
    opacity: .85
  });

  // Style the main screen
  mainScreen.style = {
    border: "2px solid white",
    borderRadius: "4px",
    boxShadow: "0px 4px 12px 0px rgba(0,0,0,0.2)"
  };

  mainScreen.centerX();

  window.onresize = function() {
    return mainScreen.centerX();
  };

  item1OriginX = 16;

  item1OriginY = 32;

  item1 = new Layer({
    width: 128,
    height: 88,
    backgroundColor: "#74a5d9",
    borderRadius: "4px",
    x: item1OriginX,
    y: item1OriginY
  });

  item1.superLayer = mainScreen;

  item1.draggable.enabled = true;

  dropAreaColor = "#df948e";

  dropAreaHoverColor = "#df4e42";

  dropArea = new Layer({
    width: mainScreenWidth - 32,
    height: mainScreenHeight / 3,
    backgroundColor: dropAreaColor,
    maxY: mainScreenHeight - 16,
    borderRadius: "4px"
  });

  dropArea.superLayer = mainScreen;

  dropArea.centerX();

  dropArea.placeBehind(item1);

  undoButton = new Layer({
    width: 104,
    height: 32,
    image: "https://s3-us-west-2.amazonaws.com/s.cdpn.io/211619/Undo_Button.png",
    midX: dropArea.midX,
    midY: dropArea.midY,
    opacity: 0
  });

  undoButton.superLayer = mainScreen;

  undoButton.sendToBack();

  //actions
  item1.on(Events.DragStart, function() {
    item1.animate({
      properties: {
        scale: 1.2
      },
      curve: "ease-in",
      time: .2
    });
    return item1.style = {
      boxShadow: "0px 2px 4px 0px rgba(0,0,0,0.6)"
    };
  });

  item1.on(Events.DragMove, function() {
    if (item1.midY > dropArea.y) {
      dropArea.backgroundColor = dropAreaHoverColor;
      return dropArea.animate({
        properties: {
          scale: 1.05
        },
        time: .2
      });
    } else {
      dropArea.backgroundColor = dropAreaColor;
      return dropArea.animate({
        properties: {
          scale: 1
        },
        time: .2
      });
    }
  });

  item1.on(Events.DragEnd, function() {
    if (item1.midY > dropArea.y) {
      //drop the item into the area
      isDropped = true;
      item1.animate({
        properties: {
          midX: dropArea.midX,
          midY: dropArea.midY,
          scale: .2,
          opacity: 0
        },
        curve: "spring( 300, 20, 0 )"
      });
      undoButton.bringToFront();
      undoButton.animate({
        properties: {
          opacity: 1
        },
        curve: "ease-in-out"
      });
    } else {
      //snap back to original position
      item1.animate({
        properties: {
          x: item1OriginX,
          y: item1OriginY,
          scale: 1
        },
        curve: "spring( 300, 15, 0 )"
      });
      item1.style = {
        boxShadow: ""
      };
    }
    dropArea.backgroundColor = dropAreaColor;
    return dropArea.animate({
      properties: {
        scale: 1
      },
      curve: "spring( 300, 15, 0 )"
    });
  });

  undoButton.on(Events.Click, function() {
    if (isDropped) {
      item1.animate({
        properties: {
          x: item1OriginX,
          y: item1OriginY,
          scale: 1,
          opacity: 1
        },
        curve: "spring( 300, 15, 0 )"
      });
      dropArea.scale = 0.95;
      dropArea.animate({
        properties: {
          scale: 1
        },
        curve: "spring( 300, 15, 0 )"
      });
      undoButton.sendToBack();
      return undoButton.opacity = 0;
    }
  });

}).call(this);


//# sourceMappingURL=matcha.js.map
//# sourceURL=coffeescript