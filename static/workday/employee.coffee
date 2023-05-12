
activateEmployee = (event) ->
    console.log 'Activate Employee Called'
    bg = document.getElementById "background"
    bg.removeEventListener 'click', deactivateEmployee
    bg.addEventListener 'click', deactivateEmployee

deactivateEmployee = (event) ->
    console.log 'Deactivate Employee Called'
    bg = document.getElementById "background"
    bg.removeEventListener 'click', deactivateEmployee
    active = document.getElementsByClassName "active"
    active.classList.remove "active"
    active.style.scale = 1


 observer = new MutationObserver (mutations) -> 
    for mutation in mutations
      if mutation.type is 'childList'
        for node in mutation.addedNodes
          if node.nodeType is Node.ELEMENT_NODE and node.classList.contains('employee')
            if $(node).data('prev-shift') is 'AM'
              $(node).addClass('bg-red-100')
              
  observer.observe document.documentElement, childList: true, subtree: true
