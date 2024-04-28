window.addEventListener('load', function () {
  const preloader = document.querySelector('.preloader');

  preloader.classList.add('hide');

  preloader.addEventListener('transitionend', function () {
    preloader.remove();
  });
});