function findGrid(btnNode) {
  while (btnNode.classList[0] !== 'gridItem') {
    btnNode = btnNode.parentNode;
  }
  return btnNode;
}

function handleSuccess(btn) {
  const grid = findGrid(btn);
  const main = document.querySelector('main');
  main.removeChild(grid);
  if (document.querySelector('main .gridItem') === null) {
    const endOfList = document.createElement('p');
    endOfList.className = 'endOfList';
    endOfList.innerText = 'Currently you have no saved artworks';
    main.prepend(endOfList);
  }
}

function handleError(err) {
  const main = document.querySelector('main');

  const alert = document.createElement('div');
  alert.className = 'alertWrapper';

  alert.innerHTML = [
    '<div class="alert alert-danger alert-dismissible" role="alert">',
    `   <div>An error occured when unsaving artwork: ${err}</div>`,
    '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
    '</div>'
  ].join('');

  if (!main.firstChild.firstChild) {
    main.prepend(alert);
  }
}

function bookmarkBtnOnClick() {
  const bookmarkBtns = document.querySelectorAll('#bookmarkBtn');
  bookmarkBtns.forEach((btn) => {
    const postId = btn.dataset.postId;
    btn.addEventListener('click', (evt) => {
      evt.preventDefault();

      $.ajax({
        url: `/unsave_post/${postId}`,
        type: 'PUT',
        success: (result) => {
          handleSuccess(btn);
        },
        error: (error) => {
          handleError(error);
        }
      });
    });
  });
}

document.addEventListener('DOMContentLoaded', (evt) => {
  bookmarkBtnOnClick();
});