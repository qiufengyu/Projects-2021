window.onscroll = function() {scrollFunction()};

function scrollFunction() {
  if (document.body.scrollTop > 64 || document.documentElement.scrollTop > 64) {
    $('nav.header-navbar').attr('style', 'background-color:#FFF;box-shadow:-8px 12px 18px 0 rgb(25 42 70 / 13%)');
  } else {
    $('nav.header-navbar').attr('style', '');
  }
}

function clearText() {
     document.getElementById("textArea").value = "";
}