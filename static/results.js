$( document ).ready(function() {

    // extract parameters for sources and wa_key:
    var wa_key = $( "param#wa-key" ).attr( "value" );
    var cat_src = {};
    var params = $( "param.cat-src" );
    for ( i = 0; i < params.length; i++) {
        var cat = params.eq( i ).attr( "name" );
        cat_src[cat] = params.eq( i ).attr( "value" ).split(' ');
    }

    console.log( "wa_key: " + wa_key);
    for ( var cat in cat_src ) {
        console.log( cat + ": " + cat_src[cat] );
    }

});
