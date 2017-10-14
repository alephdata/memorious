$(function() {
    $('.invoke').click(function(event) {
        var $el = $(event.target),
            crawler = $el.data('crawler'),
            action = $el.data('action');
        console.log($el.data('crawler'));
        event.preventDefault();
        $el.addClass('done');
        $.post('/invoke/' + crawler + '/' + action).then(function(data) {
            console.log(data);
        });
    });
});