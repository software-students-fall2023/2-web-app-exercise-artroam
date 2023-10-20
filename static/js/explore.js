$(document).ready(function () {
    // Attach a click event handler to the like buttons
    $('.like-button').click(function (event) {
        event.preventDefault();

        var button = $(this);
        var postID = button.data('post-id');
        var currentLikes = button.data('likes');

        $.ajax({
            type: 'POST',
            url: button.closest('form').attr('action'),
            data: {
                post_id: postID
            },
            success: function (data) {
                if (data.success) {
                    // Toggle the like button state
                    if (button.hasClass('liked')) {
                        button.removeClass('liked');
                        button.find('i').text('thumb_up');
                        button.data('likes', currentLikes - 1);
                    } else {
                        button.addClass('liked');
                        button.find('i').text('thumb_up_filled');
                        button.data('likes', currentLikes + 1);
                    }

                    // Update the like count
                    button.closest('.statsContainer').find('.like-count').text(data.likes);
                } else {
                    console.log('Failed to like post.');
                }
            },
            error: function () {
                console.log('Error occurred while sending the like request.');
            }
        });
    });
});