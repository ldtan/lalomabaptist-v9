jQuery(document).ready(function ($) {

  // Adjust navbar distance from the header for smaller devices.
  function calibrateNavbar() {
    if ($(window).width() >= 992) {
      return false;
    }

    var navbar = $('#siteNavbar');
    $('.offcanvas-collapse', navbar).css('top', `${navbar.outerHeight()}px`);
    return true;
  }

  // Handles the behavior of the navbar when the page is scrolled up and down.
  function scrollTransitionNavbar() {
    var navbar = $('#siteNavbar');
    var scrolltop = $(window).scrollTop();
    
    if (scrolltop <= 100 && !$('.offcanvas-collapse', navbar).hasClass('open')) {
      navbar.addClass('scrolledup');

    } else {
      navbar.removeClass('scrolledup');
    }
  }

  // Syncs the height of the navbar fill to the height of the navbar.
  function syncNavbarFill() {
    var navbar = $('#siteNavbar');
    $('#siteNavbarFill').css('height', `${navbar.outerHeight()}px`);
    console.log(navbar.outerHeight());
  }
  
  $('[data-toggle="offcanvas"], .navbar-nav > li > .nav-link').on('click', function () {
    if ($(this).hasClass('dropdown-toggle')) {
      return;
    }
    
    $('.offcanvas-collapse').toggleClass('open');
    
    if ($(window).scrollTop() <= 50) {
      $('#siteNavbar').toggleClass('scrolledup');
    }
  });

  calibrateNavbar();
  $('#siteNavbar').on('resize', calibrateNavbar);

  scrollTransitionNavbar();
  $(window).on('scroll', scrollTransitionNavbar);

  syncNavbarFill();
  $('#siteNavbar').on('resize', syncNavbarFill);
});