// This is a function which starts at the very beginning when the webpage is laoded. 
function loadSavedPosts() {
    $.ajax({
        url: "/get_saved_posts",
        method: "GET",
        success: function (data) {
            var savedPosts = data.saved_posts;

            $("button[name='saveButton']").each(function () {
                var postID = $(this).data('post-id');
                var button = $(this);

                if (savedPosts.includes(postID)) {
                    button.css("background-color", "#fdd68f");
                }
            });
        },
        error: function (err) {
            console.log('Error loading saved posts:', err);
        }
    });
}

// This is a function which srarts at the very beginning when the webpage is loaded. 
function loadLikeCounts() {
    $("button[name='likeButton']").each(function () {
        var postID = $(this).data('post-id');
        var likeCount = $(".like-count[data-post-id='" + postID + "']");
        
        // Here we use AJAX to get the like counts for each post
        $.ajax({
            url: "/get_like_count/" + postID,
            method: "GET",
            success: function (data) {
                if (likeCount) {
                    likeCount.text(data.likes);
                }
            },
            error: function (err) {
                console.log('Error loading like counts:', err);
            }
        });
    });
}


// When the HTML page loads do the following: 
$(document).ready(function () {
    // When the likeButton is pressed, it will get the postID from the like button associated with the post
    $("button[name='likeButton']").click(function () {
        var postID = $(this).data('post-id');
        var button = $(this); //Reference to the button clicked
        var likeCount = $(".like-count[data-post-id='" + postID + "']"); //Reference for the likeCount for the post
        
        // Here we use AJAX to update the webpage in real time, no reloading page
        $.ajax({
            url: "/like_post/" + postID,
            method: "POST",

            // When AJAX request is a success:
            success: function (data) {
                if (data.redirect) {
                    window.location.href = data.redirect;  // Redirect to the URL sent by the server which would be the login page if the user_id is None.
                }

                // Updates the like value in realtime on the webpage
                if (likeCount) {
                    likeCount.text(data.likes);
                }

                // If the data is liked, it changes the colour to Yellow, if not, it removes the colour. 
                if (data.liked) {
                    button.css("background-color", "#fdd68f")
                } 
                
                else {
                    button.css("background-color", "#FFA500")
                }
            },


            error: function (xhr, status, error) {
                console.log("Error status: " + status);
                console.log("Error message: " + error);
            }
        });
    });

    // This is a function for the save button
    $("button[name='saveButton']").click(function() {
        var postID = $(this).data('post-id');
        var button = $(this);
        
        $.ajax({
            url: "/save_post/" + postID,
            method: "POST",

            // When AJAX request is a success:
            success: function(data) {
                if (data.redirect) {
                    window.location.href = data.redirect;  // Redirect to the URL sent by the server which would be the login page if the user_id is None.
                }

                // If we save the post into the gallery then change the icon color
                if (data.saved) {
                    button.css("background-color", "#fdd68f")
                } 
                
                else {
                    button.css("background-color", "#FFA500")
                }
            },

            error: function(err) {
                console.log('Error saving post:', err);
            }
        });
    }); 


    // Load saved posts when the page loads
    loadSavedPosts();

    // Load the likes number per each post: 
    loadLikeCounts()
});