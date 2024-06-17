const div1 = document.getElementById("log");
const div2 = document.getElementById("reg");

div1.addEventListener('click', function() {
    div1.classList.add('toggle-border');
    div2.classList.remove('toggle-border'); // Remove border from button2
});

div2.addEventListener('click', function() {
    div2.classList.add('toggle-border');
    div1.classList.remove('toggle-border'); // Remove border from button1
});

function toggleContent(id) {
    var content1 = document.getElementById('content1'); // Get the content element for Button 1
    var content2 = document.getElementById('content2'); // Get the content element for Button 2
    
    if (id === 'content1') {
        content1.style.display = 'block'; // Display content for Button 1
        content2.style.display = 'none'; // Hide content for Button 2
    } else if (id === 'content2') {
        content1.style.display = 'none'; // Hide content for Button 1
        content2.style.display = 'block'; // Display content for Button 2
    }

}