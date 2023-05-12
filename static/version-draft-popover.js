// add event listener for click to the #versionEllipsis element
document.getElementById('versionEllipsis').addEventListener('click', function() {
    // get the popover element
    // if the popover is hidden, show it
    var popover = document.getElementById('versionPopover');
    
        if (popover.style.display === 'none') {
            popover.style.display = 'block';
            // set the popover's position to the bottom of the #versionEllipsis screen position 
            popover.style.top = document.getElementById('versionEllipsis').getBoundingClientRect().bottom + 'px';
            popover.style.left = document.getElementById('versionEllipsis').getBoundingClientRect().left + 'px';
        // wait 500ms, then make event listener for a click outside the popover
        setTimeout(function() { 
            document.addEventListener('click', function(event) {
                // if the click is outside the popover, hide it
                if (!popover.contains(event.target)) {
                    popover.style.display = 'none';
                    // remove the event listener
                    document.removeEventListener('click', arguments.callee);
                }   
            });
        }, 500);
            
        } else {
            // otherwise, hide it
            popover.style.display = 'none';
            }
        }
);





