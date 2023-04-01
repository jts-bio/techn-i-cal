showContextMenu = (ev) ->
  console.log 'CtxtMenu Called'
  contextMenu = document.getElementById "contextMenu"

  contextMenu.style.display = "block"
  contextMenu.style.left    = ev.pageX + "px"
  contextMenu.style.top     = ev.pageY + "px"
  # remove previous event listener if exists
  document.removeEventListener 'mousedown', hideContextMenu
  # then remake it and apply to document
  document.addEventListener    'mousedown', hideContextMenu

hideContextMenu = (ev) ->
  contextMenu = document.getElementById "contextMenu"
  contextMenu.style.display = "none"


# Add event listeners on document ready 
document.addEventListener 'DOMContentLoaded', ->
  document.addEventListener 'contextmenu', showContextMenu


  