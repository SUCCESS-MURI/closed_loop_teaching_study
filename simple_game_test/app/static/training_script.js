$('.carousel').on('slide.bs.carousel', function(e) {

    var slidingItemsAsIndex = $('.carousel-item').length - 1;

    // If last item hide next arrow
    if ($(e.relatedTarget).index() == slidingItemsAsIndex) {
        $('.carousel-control-next').hide();
    } else {
        $('.carousel-control-next').show();
    }

    // If first item hide prev arrow
    if ($(e.relatedTarget).index() == 0) {
        $('.carousel-control-prev').hide();
    } else {
        $('.carousel-control-prev').show();
    }

})