// author: JOSH STEINBECKER
//
// -************************************
// TOASTY.JS
// -************************************
//
// A simple javascript tool for creating and displaying
// toast messages in a Django application.
//
// written originally 
// for the FlowRate Schedule Management project
//


function showToast(message, type) {
            //
            // create the toast element
            var toast = document.createElement("div");
            
            // create the toast icon
            toast.classList.add("flex", 
                                "items-center", 
                                "w-full", 
                                "max-w-xs", 
                                "px-4",
                                "py-2",
                                "mb-4", 
                                "text-zinc-900", 
                                "bg-zinc-200", 
                                "rounded-lg",
                                "text-sm",
                            );
        
            var icon = document.createElement("i");
            icon.classList.add("fa-duotone","font-bold","mr-2");
            if (type == "success" || type == "s") {
                icon.classList.add("fa-check-circle");
                toast.classList.add('bg-green-100', 'text-green-800', 'dark:bg-green-800', 'dark:text-green-100');
            } else if (type == "error" || type == "e") {
                icon.classList.add("fa-times-circle");
                toast.classList.add('bg-amber-100', 'text-red-800', 'dark:bg-red-800', 'dark:text-red-100');
            } else if (type == "warning" || type == "w" || type == "warn") {
                icon.classList.add("fa-exclamation-circle");
                toast.classList.add('bg-amber-100', 'text-amber-800', 'dark:bg-amber-800', 'dark:text-amber-100');
            } else if (type == "info" || type == "i" || type == "information") {
                icon.classList.add("fa-info-circle");
                toast.classList.add('bg-blue-100', 'text-blue-800', 'dark:bg-blue-800', 'dark:text-blue-100');
            }
            // create the toast span
            var titlespan = document.createElement("span");
            titlespan.classList.add("font-extrabold",
                                    "text-2xs",
                                    "text-white",
                                    "uppercase");

            var toastspan = document.createElement("span");
            toastspan.classList.add("toast-span",
                                    "font-bold",
                                    "jbm");
            // set the toast type
            if (type == "success") {
                toastspan.classList.add("toast-span-success");
                toast.classList.add("bg-emerald-100", "text-emerald-800");
            } else if (type == "error") {
                toastspan.classList.add("toast-span-error");
                toast.classList.add("bg-red-100", "text-red-800");
            } else if (type == "info") {
                toastspan.classList.add("toast-span-info");
                toast.classList.add("bg-sky-100", "text-sky-800");
            }
            // add the toast span to the toast
            toast.appendChild(icon);
            toast.appendChild(titlespan);
            toast.appendChild(toastspan);
            toast.appendChild(document.createTextNode(message));
            // add the toast to the wrapper
            var wrapper = document.getElementById("toast-wrapper");
            wrapper.appendChild(toast);
            // slide the toast in from the bottom
            toast.style.bottom = "-8x";
            toast.style.opacity = 0;
            setTimeout(function() {
                toast.style.bottom = "20px";
                toast.style.opacity =0.85;
            }, 50);
            // remove the toast after 5 seconds
            setTimeout(function() {
                wrapper.removeChild(toast);
            }, 8000);
}

function mouseOverToast (toast) {
            // reset the time unitl removeChild 
            toast.style.opacity = 1;
            toast.style.transition = "none";
            // remove the toast after 5 seconds
            setTimeout(function() {
                toast.style.transition = "all 0.5s ease";
                toast.style.opacity = 0;
                setTimeout(function() {
                var wrapper = document.getElementById("toast-wrapper");
                wrapper.removeChild(toast);
                }, 500);
            }, 5000);
}




// create eventlistener 
document.addEventListener("DOMContentLoaded", function() {
    // get all the toasts
    var toasts = document.getElementsByClassName("my-toast");
    // loop through the toasts
    for (var i = 0; i < toasts.length; i++) {
        // add eventlistener to each toast
        toasts[i].addEventListener("mouseover", function() {
        mouseOverToast(this);
        });
    }
    });
