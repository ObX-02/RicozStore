document.addEventListener("DOMContentLoaded", function () {

```
const sidebar = document.querySelector(".dashboard-sidebar");
const toggle = document.getElementById("sidebarToggle");

if (!sidebar || !toggle) {
    return;
}

toggle.addEventListener("click", function () {
    sidebar.classList.toggle("sidebar-open");
});

document.addEventListener("click", function (event) {

    if (window.innerWidth > 900) {
        return;
    }

    const clickedInsideSidebar = sidebar.contains(event.target);
    const clickedToggle = toggle.contains(event.target);

    if (!clickedInsideSidebar && !clickedToggle) {
        sidebar.classList.remove("sidebar-open");
    }
});

window.addEventListener("resize", function () {

    if (window.innerWidth > 900) {
        sidebar.classList.remove("sidebar-open");
    }

});
```

});
