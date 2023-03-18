wdid_elem =     document.querySelector '#wdid'
ptolist_elem =  document.querySelector '#pto-list'

# Constants ~~
employees =     document.querySelectorAll '.employee'
wdid =          wdid_elem.dataset.value
ptolist =       ptolist_elem.dataset.employees.split ' '
    # ptolist is a LIST of empl SLUGS

# Logs ~~ 
console.log     "workdayId", wdid
console.log     "PTO", ptolist.length , (empl for empl in ptolist)

# Functions ~~
printds      = (obj) -> console.log JSON.stringify obj.dataset, null, 2
getAvailable = (obj) -> obj.dataset.available.split ' '

addPtoBadges = ->
    for empl in employees
        if empl.dataset.employeeId in ptolist
            console.log 'PTO', empl.dataset.employeeId
            empl.classList.add 'bg-red-900','ring', 'ring-red-400', 'bg-opacity-25'
            # create badge
            badge = document.createElement 'span'
            empl.appendChild badge
            badge.classList.add 'badge-top-right', 'bg-red-900', 'text-white'
            badge.classList.add 'text-xs', 'font-bold', 'rounded', 'px-2', 'py-1', 
            badge.classList.add 'shadow', 'ring-1', 'ring-black'

            badge.innerHTML = 'PTO'
            
addPtoBadges()



