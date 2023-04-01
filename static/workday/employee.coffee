
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
        
