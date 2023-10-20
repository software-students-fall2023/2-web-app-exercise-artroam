// Starts when the HTML page is loaded: 
$(document).ready(function () {
    $(".like-form").submit(function (event) {
        //This removes the default submission actino a regular form does. 
        event.preventDefault(); 

        // Sets up variables for the post_id, the likeButton and an array of all liked posts
        var post_id = $(this).data("post-id");
        var likeButton = $(this).find(".like-button");
        var likedPosts = JSON.parse(localStorage.getItem("likedPosts")) || [];
        
        // If the array includes a post (meaning user has already liked it) and they click on it, we unlike it
        if (likedPosts.includes(post_id)) {
            // Send a request to the server to decrement likes, hence the form will submit 'unlike'
            $.post("/like", { post_id: post_id, action: "unlike" }, function (data) {
                if (data.success) {
                    likedPosts = likedPosts.filter(function (id) {
                        return id !== post_id;
                    });
                    localStorage.setItem("likedPosts", JSON.stringify(likedPosts));
                    likeButton.find("i").text("thumb_up");
                }
            });
        } 
        
        // Else the post isn't in the liked array so then we make the user like it. 
        else {
            // Send a request to the server to increment likes, hence the form will submit 'like'
            $.post("/like", { post_id: post_id, action: "like" }, function (data) {
                if (data.success) {
                    likedPosts.push(post_id);
                    localStorage.setItem("likedPosts", JSON.stringify(likedPosts));
                    likeButton.find("i").text("thumb_down");
                }

                // Update the like count on the page without reloading the entire page.
                var likeCountElement = likeButton.siblings("span");
                var currentLikeCount = parseInt(likeCountElement.text(), 10);
                likeCountElement.text(currentLikeCount + 1); // Update the like count.
            });
        }
    });
});
