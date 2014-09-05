$( document ).ready(function() {

    // extract parameters for sources and wa_key:
    var pmap = {
        wa_key: $( "param#wa-key" ).attr( "value" ),
        search_str: $( "param#search-str" ).attr( "value" ),
        match_score: $( "param#match-score" ).attr( "value" ),
        min_wc: $( "param#min-wc" ).attr( "value" ),
        back_days: $( "param#back-days" ).attr( "value" )
    };
    var cat_src = {};
    var params = $( "param.cat-src" );
    for ( i = 0; i < params.length; i++) {
        var cat = params.eq( i ).attr( "name" );
        cat_src[cat] = params.eq( i ).attr( "value" ).split(' ');
    }

    var job_id = null;
    // intial call: submit parameters and get job-id:
    $.ajax({
        url: 'scorematches',
        data: pmap,
        type: 'GET',
        dataType: 'json',
        success: function( json ) {
            job_id = json.job_id;
            console.log( "job_id: " + job_id );
        },
        eror: function( xhr, status, errorThrown ) {
            console.log( "Error: " + errorThrown );
            console.log( "Status: " + status );
            console.dir( xhr );
        },
        complete: function( xhr, status ) {
            alert( "The request is complete!" );
        }
    });


    // now check for results
    (function pollForID() {
        if ( job_id == null ) {
            setTimeout(pollForID, 500);
        }
        else {
            $.ajax({
                url: 'scorematches',
                data: {'job_id': job_id},
                type: 'GET',
                dataType: 'json',
                success: function( json ) {
                    console.log( "status: " + json.status );
                    console.log( "result: " + json.result );
                    if ( json.status !== 'finished' ) {
                        setTimeout(pollForID, 1000);
                    }
                },
                eror: function( xhr, status, errorThrown ) {
                    console.log( "Error: " + errorThrown );
                    console.log( "Status: " + status );
                    console.dir( xhr );
                },
                complete: function( xhr, status ) {
                    alert( "The request is complete!" );
                }
            });
        }
    }());

});
