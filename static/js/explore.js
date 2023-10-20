const filterButton = document.getElementById("filterButton");
const filterContents = document.querySelector(".filter_menu .filter_contents");

let isOpen = false;

filterButton.addEventListener("click", function (e) {
    e.stopPropagation();
    isOpen = !isOpen;

    if (isOpen) {
        filterContents.style.display = "block";
    } else {
        filterContents.style.display = "none";
    }
});

document.addEventListener("click", function () {
    if (isOpen) {
        filterContents.style.display = "none";
        isOpen = false;
    }
});
