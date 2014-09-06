$(document).ready(function() {

    // extract parameters for sources and wa_key:
    // NOTE: need to also provide prios so we can sequence
    // submissions accordingly
    var pmap = {
        wa_key: $("param#wa-key").attr("value"),
        search_str: $("param#search-str").attr("value"),
        match_score: $("param#match-score").attr("value"),
        min_wc: $("param#min-wc").attr("value"),
        back_days: $("param#back-days").attr("value")
    };
    var cat_src = {};
    var params = $("param.cat-src");
    for (var i = 0; i < params.length; i++) {
        var cat = params.eq(i).attr("name");
        cat_src[cat] = params.eq(i).attr("value").split(' ');
    }

    // set up "score board"
    var score_board = {};
    var score_board_size = 0;
    for (cat in cat_src) {
        var num_src = cat_src[cat].length;
        for (var i = 0; i < num_src; i++) {
            score_board[cat_src[cat][i]] = {
                'cat': cat,
                'job_id': null,
                'status': 0,
                'result': null
            };
            score_board_size++;
        }
    }
    var score_board_fill = 0;

    // intial call: submit parameters and get job-id:
    for (var src in score_board) {
        pmap['src'] = src;
        $.ajax({
            url: 'scorematches',
            data: pmap,
            type: 'GET',
            dataType: 'json',
            success: function(json) {
                score_board[json.src].job_id = json.job_id;
            },
            eror: function(xhr, status, errorThrown) {
                console.log("Error: " + errorThrown);
                console.log("Status: " + status);
                console.dir(xhr);
            },
            complete: function(xhr, status) {
                console.log("submitted: " + xhr.responseText);
            }
        });
    }

    // now check for results:
    var fetch_timeout = 500;
    for (var src in score_board) {
        function pollForID(src) {
            return function() {
                if (score_board[src].job_id == null) {
                    setTimeout(pollForID(src), fetch_timeout);
                }
                else {
                    $.ajax({
                        url: 'scorematches',
                        data: {'src': src, 'job_id': score_board[src].job_id},
                        type: 'GET',
                        dataType: 'json',
                        success: function(json) {
                            if (json.status == 'finished') {
                                score_board[json.src].status = 1;
                                score_board[json.src].result = json.result;
                            }
                            else {
                                var timeout = fetch_timeout + 2000 * (1 - score_board_fill);
                                setTimeout(pollForID(src), timeout);
                            }
                        },
                        eror: function(xhr, status, errorThrown) {
                            console.log("Error: " + errorThrown);
                            console.log("Status: " + status);
                            console.dir(xhr);
                        },
                        complete: function(xhr, status) {
                            console.log("fetched: " + xhr.responseText);
                        }
                    });
                }
            };
        }
        setTimeout(pollForID(src), fetch_timeout);
    }

    // check score board:
    function keep_score() {
        var fin_count = 0;
        for (var src in score_board) {
            if (score_board[src].status == 1) {
                ++fin_count;
            }
        }
        score_board_fill = fin_count / score_board_size;
        if (fin_count < score_board_size) {
            var timeout = fetch_timeout + 2000 * (1 - score_board_fill);
            console.log("fin_count: " + fin_count);
            console.log("setting keep_score timeout to " + timeout + "ms");
            setTimeout(keep_score, timeout);
        }
    }
    setTimeout(keep_score, fetch_timeout);

});

