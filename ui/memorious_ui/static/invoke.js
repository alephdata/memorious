$(function() {
    $('.invoke').click(function(event) {
        var $el = $(event.target),
            crawler = $el.data('crawler'),
            action = $el.data('action');
        console.log($el.data('crawler'));
        event.preventDefault();
        $.post('/invoke/' + crawler + '/' + action).then(function(data) {
            console.log(data);
            if (action === 'run'){
                $el.children('.fa').removeClass('fa-play').addClass('fa-ban');
                $el.get(0).childNodes[2].nodeValue = 'Cancel';
                $el.data('action', 'cancel')
            }
            if (action === 'cancel'){
                $el.children('.fa').removeClass('fa-ban').addClass('fa-play');
                $el.get(0).childNodes[2].nodeValue = 'Run';
                $el.data('action', 'run');
            }
        });
    });
});