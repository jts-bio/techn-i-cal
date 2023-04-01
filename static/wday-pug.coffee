# 'wday/views.py'

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

behavior Employee
  init: ->
    @trigger 'checkFlags'
    
    if @data.employeeId in $('#pto-list').data('employees')
      @data.pto = true
      $('<span>').addClass('pto-flag').text('PTO').appendTo(@)
    
    @data.weekHours = if @data.weekHours? then parseInt(@data.weekHours) else 0
    @data.periodHours = if @data.periodHours? then parseInt(@data.periodHours) else 0
    $('.hours-display', @).text("#{@data.weekHours}/#{@data.periodHours} hrs")

  onClick: (event) ->
    event.stopPropagation()
    if not @.hasClass('active')
      @.transition('scale', 1, 200)
      .addClass('active')
      .siblings('.employee').removeClass('active')
      .end().transition('scale', 1.25, 300)
      .trigger('hideHint', '.slot')
      .trigger('showHint', '.slot')
      console.log JSON.stringify(@.data(), null, 2)
    else
      @.removeClass('active')
      .transition('scale', 1, 300)
      .trigger('hideHint', '.slot')

  onDragstart: (event) ->
    event.originalEvent.dataTransfer.setData('text', @data.employeeId)
    @.siblings('.employee').removeClass('active')
    if not @.hasClass('active')
      @.addClass('active')
    .trigger('hideHint', '.slot')
    .trigger('showHint', '.slot')
    console.log @data.available

  onDragend: ->
    @.trigger('hideHint', '.slot')
    .delay(500).queue(-> @.removeClass('active'); @.dequeue())

  onShowBooted: ->
    for i in [1..4]
      @.addClass('bg-amber-700')
      .delay(300).queue(-> @.removeClass('bg-amber-700'); @.dequeue())
      .delay(300)

  onShowAccepted: ->
    for i in [1..4]
      @.addClass('bg-emerald-700')
      .delay(300).queue(-> @.removeClass('bg-emerald-700'); @.dequeue())
      .delay(300)

  onCheckFlags: ->
    arrowClass = (type) ->
      switch type
        when 'AM' then ['text-yellow-400', 'opacity-50']
        when 'PM' then ['text-sky-400', 'opacity-50']
        else []

    $('.prev-arrow', @).toggleClass(arrowClass(@data.prevDay).join(' ')).removeClass('text-white')
    $('.next-arrow', @).toggleClass(arrowClass(@data.nextDay).join(' ')).removeClass('text-white')

    if ['PM', 'XN'].includes(@data.inDaytime) and @data.nextDay is 'AM'
      @.addClass('bg-orange-900 bg-opacity-40')

    if @data.inDaytime is 'AM' and @data.prevDay is 'PM'
      @.addClass('bg-orange-900 bg-opacity-40')

  onUnfocus: ->
    @.removeClass('active')
    .transition('scale', 1, 300)
    .trigger('hideHint', '.slot')

  onDblclick: (event) ->
    event.stopPropagation()
    resp = JSON.stringify(@.data(), null, 2)
    alert(resp)
# apply behavior to all .employee elements
$('.employee').behavior(Employee)
